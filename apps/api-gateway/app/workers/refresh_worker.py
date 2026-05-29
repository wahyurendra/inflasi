"""Incremental feature + forecast refresh after crowd reports flow into the fact table.

Consumes ``stream:validation_done``. For each event where the validator wrote a
new row into ``fact_price_daily`` (``fact_written == "1"``), debounces the pair
(commodity_id, region_id) for ~15 minutes, then re-runs the feature builder
scoped to those pairs and refreshes their forecasts (h=7, 14, 30 in one
ml-gateway round-trip).

Design notes
------------
* In-process under the FastAPI lifespan, mirroring :class:`ValidationPipeline`.
  Shares the Redis client + DB pool; the debounce buffer is naturally ephemeral.
  If a pod restarts the next nightly full materialize is the safety net.
* Two cooperating asyncio tasks under one gather: a cheap consume loop that
  acks immediately and updates an in-memory pending dict, plus a flush loop
  that periodically drains it.
* ml-gateway is the rate-limited dependency, so per-flush work runs through an
  asyncio.Semaphore (default 4 concurrent pairs) and is capped at
  ``max_per_flush`` pairs per cycle; overflow rolls to the next cycle.
* Graceful degradation: any Redis hiccup retries, any pair-level error is
  logged and isolated to that pair.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date

from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import text

from app.core.redis import get_redis
from app.database import async_session
from app.services.feature_builder import FeatureBuilder
from app.services.prediction_service import PredictionService

logger = logging.getLogger("refresh_worker")

STREAM_DONE = "stream:validation_done"
GROUP = "refresh_workers"

_FLUSH_INTERVAL_S = 900       # 15 min — matches the user's "hourly mini-batch" choice (sub-hourly)
_FLUSH_TICK_S = 60            # how often the flush loop wakes to check the buffer
_MAX_BUFFER = 200             # trigger early flush when buffer fills
_PER_FLUSH_CONCURRENCY = 4    # cap simultaneous ml-gateway calls
_MAX_PER_FLUSH = 50           # cap pairs processed per cycle; overflow rolls to next
_BUFFER_HARD_CAP = 1000       # drop oldest beyond this to keep memory bounded


class RefreshWorker:
    def __init__(self) -> None:
        self._task: "asyncio.Task | None" = None
        self._stop = asyncio.Event()
        self._pending: dict[tuple[int, int], float] = {}
        self._pending_lock = asyncio.Lock()

    async def start(self) -> None:
        redis = get_redis()
        try:
            await redis.xgroup_create(STREAM_DONE, GROUP, id="0", mkstream=True)
        except Exception:
            pass  # consumer group already exists
        self._stop.clear()
        self._task = asyncio.create_task(self._run())
        logger.info("RefreshWorker started")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("RefreshWorker stopped")

    async def _run(self) -> None:
        try:
            await asyncio.gather(self._consume_loop(), self._flush_loop())
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("RefreshWorker crashed")

    # ── Consume ──────────────────────────────────────────────

    async def _consume_loop(self) -> None:
        redis = get_redis()
        consumer = f"refresh-{id(self)}"
        while not self._stop.is_set():
            try:
                resp = await redis.xreadgroup(
                    GROUP, consumer, {STREAM_DONE: ">"},
                    count=50, block=5000,
                )
                for _stream, entries in resp or []:
                    for msg_id, data in entries:
                        try:
                            await self._enqueue(data)
                        except Exception:
                            logger.exception("enqueue failed for %s", data)
                        finally:
                            await redis.xack(STREAM_DONE, GROUP, msg_id)
            except asyncio.CancelledError:
                break
            except RedisTimeoutError:
                continue
            except Exception:
                logger.exception("consume loop error; retrying")
                await asyncio.sleep(5)

    async def _enqueue(self, data: dict) -> None:
        if data.get("status") != "APPROVED" or data.get("fact_written") != "1":
            return
        try:
            cid = int(data["commodity_id"])
            rid = int(data["region_id"])
        except (KeyError, ValueError):
            return
        async with self._pending_lock:
            self._pending[(cid, rid)] = time.time()
            if len(self._pending) > _BUFFER_HARD_CAP:
                # Drop oldest to keep memory bounded; nightly batch is the safety net.
                oldest = sorted(self._pending.items(), key=lambda kv: kv[1])[:_BUFFER_HARD_CAP // 2]
                for key, _ in oldest:
                    self._pending.pop(key, None)
                logger.warning("refresh buffer overflow; dropped %s oldest pairs", len(oldest))

    # ── Flush ────────────────────────────────────────────────

    async def _flush_loop(self) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.sleep(_FLUSH_TICK_S)
                if self._stop.is_set():
                    break
                if not await self._should_flush():
                    continue
                pairs = await self._drain()
                if not pairs:
                    continue
                await self._process_batch(pairs)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("flush loop error; continuing")

    async def _should_flush(self) -> bool:
        async with self._pending_lock:
            if not self._pending:
                return False
            if len(self._pending) >= _MAX_BUFFER:
                return True
            oldest = min(self._pending.values())
            return (time.time() - oldest) >= _FLUSH_INTERVAL_S

    async def _drain(self) -> list[tuple[int, int]]:
        async with self._pending_lock:
            items = sorted(self._pending.items(), key=lambda kv: kv[1])
            take = items[:_MAX_PER_FLUSH]
            for key, _ in take:
                self._pending.pop(key, None)
            return [key for key, _ in take]

    async def _process_batch(self, pairs: list[tuple[int, int]]) -> None:
        logger.info("refresh batch: %s pairs", len(pairs))
        sem = asyncio.Semaphore(_PER_FLUSH_CONCURRENCY)

        async def _one(pair: tuple[int, int]) -> None:
            async with sem:
                await self._refresh_pair(pair)

        await asyncio.gather(*(_one(p) for p in pairs))

    async def _refresh_pair(self, pair: tuple[int, int]) -> None:
        cid, rid = pair
        try:
            async with async_session() as db:
                codes = await self._resolve_kodes(db, cid, rid)
                if codes is None:
                    logger.warning("refresh: cannot resolve dim codes for (c=%s, r=%s)", cid, rid)
                    return
                ckode, rkode = codes

                builder = FeatureBuilder(db)
                n = await builder.build(
                    target_date=date.today(),
                    commodity_kodes=[ckode],
                    region_kodes=[rkode],
                )
                logger.debug("refresh: built %s feature rows for (c=%s, r=%s)", n, cid, rid)

                service = PredictionService(db)
                points = await service.forecast_pair_all_horizons(
                    commodity_id=cid, region_id=rid,
                )
                await db.commit()
                logger.info(
                    "refresh: (c=%s, r=%s) features=%s forecast_points=%s",
                    cid, rid, n, len(points),
                )
        except Exception:
            logger.exception("refresh_pair failed for (c=%s, r=%s)", cid, rid)

    @staticmethod
    async def _resolve_kodes(db, commodity_id: int, region_id: int) -> "tuple[str, str] | None":
        row = (await db.execute(
            text(
                """
                SELECT
                  (SELECT kode_komoditas FROM dim_commodity WHERE id = :cid) AS ckode,
                  (SELECT kode_wilayah   FROM dim_region    WHERE id = :rid) AS rkode
                """
            ),
            {"cid": commodity_id, "rid": region_id},
        )).first()
        if not row or not row.ckode or not row.rkode:
            return None
        return row.ckode, row.rkode
