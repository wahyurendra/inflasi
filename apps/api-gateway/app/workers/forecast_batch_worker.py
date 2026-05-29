"""Redis-Streams consumer that runs `batch_forecast` on demand.

Triggered by an admin write to `stream:forecast_requested` (see
`admin_models.batch_run`). The actual work lives in
:mod:`app.tasks.batch_forecast`; this worker only does the consume/dispatch
plumbing and reports completion to `stream:forecast_done`.

Lifecycle and graceful-degradation match `RefreshWorker` / `ValidationPipeline`:
in-process under the FastAPI lifespan, shares the singleton Redis client, retries
through `RedisTimeoutError`, and isolates per-message failures from the loop.

The consumer is intentionally single-replica per request — batches are heavy
and we don't want two pods racing on the same trigger.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict

from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.redis import get_redis
from app.tasks.batch_forecast import run_batch_forecast

logger = logging.getLogger("forecast_batch_worker")

STREAM_REQ = "stream:forecast_requested"
STREAM_DONE = "stream:forecast_done"
GROUP = "forecast_batch_workers"

_JOB_KEY_TTL_S = 60 * 60 * 24  # 24h for status lookups


class ForecastBatchWorker:
    def __init__(self) -> None:
        self._task: "asyncio.Task | None" = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        redis = get_redis()
        try:
            await redis.xgroup_create(STREAM_REQ, GROUP, id="0", mkstream=True)
        except Exception:
            pass  # consumer group already exists
        self._stop.clear()
        self._task = asyncio.create_task(self._loop())
        logger.info("ForecastBatchWorker started")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ForecastBatchWorker stopped")

    async def _loop(self) -> None:
        redis = get_redis()
        consumer = f"forecast-batch-{id(self)}"
        while not self._stop.is_set():
            try:
                resp = await redis.xreadgroup(
                    GROUP, consumer, {STREAM_REQ: ">"}, count=4, block=5000,
                )
                for _stream, entries in resp or []:
                    for msg_id, data in entries:
                        try:
                            await self._handle(data)
                        except Exception:
                            logger.exception("forecast batch handler failed: %s", data)
                        finally:
                            await redis.xack(STREAM_REQ, GROUP, msg_id)
            except asyncio.CancelledError:
                break
            except RedisTimeoutError:
                continue
            except Exception:
                logger.exception("forecast batch consume loop error; retrying")
                await asyncio.sleep(5)

    async def _handle(self, data: dict) -> None:
        job_id = data.get("job_id") or f"batch-{int(time.time())}"
        horizons = _parse_int_list(data.get("horizons"))
        pair_limit = _opt_int(data.get("pair_limit"))
        concurrency = _opt_int(data.get("concurrency")) or 4
        window_days = _opt_int(data.get("window_days")) or 7

        redis = get_redis()
        status_key = f"job:batch_forecast:{job_id}"
        await redis.hset(status_key, mapping={
            "status": "RUNNING",
            "started_at": str(time.time()),
        })
        await redis.expire(status_key, _JOB_KEY_TTL_S)

        logger.info("forecast batch start: job=%s horizons=%s", job_id, horizons)
        try:
            result = await run_batch_forecast(
                horizons=horizons or None,
                pair_limit=pair_limit,
                concurrency=concurrency,
                window_days=window_days,
            )
            payload = asdict(result)
            await redis.hset(status_key, mapping={
                "status": "SUCCESS",
                "finished_at": str(time.time()),
                "result": json.dumps(payload),
            })
            await redis.expire(status_key, _JOB_KEY_TTL_S)
            await redis.xadd(STREAM_DONE, {
                "job_id": job_id,
                "status": "SUCCESS",
                "result": json.dumps(payload),
            })
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            logger.exception("forecast batch failed: job=%s", job_id)
            await redis.hset(status_key, mapping={
                "status": "FAILED",
                "finished_at": str(time.time()),
                "error": err,
            })
            await redis.expire(status_key, _JOB_KEY_TTL_S)
            await redis.xadd(STREAM_DONE, {
                "job_id": job_id, "status": "FAILED", "error": err,
            })


def _parse_int_list(raw) -> list[int]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw]
    return [int(x) for x in str(raw).split(",") if x.strip()]


def _opt_int(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None
