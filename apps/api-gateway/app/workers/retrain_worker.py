"""Redis-Streams consumer that drives `retrain_models` on demand.

Triggered by an admin POST that pushes to `stream:model_retrain`. The work
itself — exporting the snapshot, spawning the trainer subprocess, finishing
the audit row — lives in :mod:`app.tasks.retrain_models`.

Status is mirrored to `job:retrain:{run_id}` so an operator can poll progress
without reading the row from Postgres on every refresh.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict

from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.redis import get_redis
from app.tasks.retrain_models import SUPPORTED_MODEL_TYPES, run_retrain

logger = logging.getLogger("retrain_worker")

STREAM_REQ = "stream:model_retrain"
GROUP = "retrain_workers"

_JOB_KEY_TTL_S = 60 * 60 * 72  # 72h — retraining is rare and audit is valuable


class RetrainWorker:
    def __init__(self) -> None:
        self._task: "asyncio.Task | None" = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        redis = get_redis()
        try:
            await redis.xgroup_create(STREAM_REQ, GROUP, id="0", mkstream=True)
        except Exception:
            pass
        self._stop.clear()
        self._task = asyncio.create_task(self._loop())
        logger.info("RetrainWorker started")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("RetrainWorker stopped")

    async def _loop(self) -> None:
        redis = get_redis()
        consumer = f"retrain-{id(self)}"
        while not self._stop.is_set():
            try:
                resp = await redis.xreadgroup(
                    GROUP, consumer, {STREAM_REQ: ">"}, count=1, block=5000,
                )
                for _stream, entries in resp or []:
                    for msg_id, data in entries:
                        try:
                            await self._handle(data)
                        except Exception:
                            logger.exception("retrain handler failed: %s", data)
                        finally:
                            await redis.xack(STREAM_REQ, GROUP, msg_id)
            except asyncio.CancelledError:
                break
            except RedisTimeoutError:
                continue
            except Exception:
                logger.exception("retrain consume loop error; retrying")
                await asyncio.sleep(5)

    async def _handle(self, data: dict) -> None:
        model_type = (data.get("model_type") or "").strip()
        if model_type not in SUPPORTED_MODEL_TYPES:
            logger.warning("retrain: unsupported model_type=%r; skipping", model_type)
            return

        horizon = _opt_int(data.get("horizon"))
        target_type = data.get("target_type") or "price"
        train_window = _opt_int(data.get("train_window_days")) or 365
        dry_run = _truthy(data.get("dry_run"))
        run_name = data.get("run_name") or None
        notes = data.get("notes") or None
        extra_args = _split_extra(data.get("extra_args"))

        logger.info(
            "retrain start: type=%s horizon=%s target=%s dry_run=%s",
            model_type, horizon, target_type, dry_run,
        )
        result = await run_retrain(
            model_type=model_type,
            horizon=horizon,
            target_type=target_type,
            train_window_days=train_window,
            run_name=run_name,
            notes=notes,
            extra_args=extra_args,
            dry_run=dry_run,
        )
        await self._publish_status(result)

    async def _publish_status(self, result) -> None:
        redis = get_redis()
        key = f"job:retrain:{result.run_id}"
        payload = asdict(result)
        await redis.hset(key, mapping={
            "status": result.status,
            "model_type": result.model_type,
            "horizon": str(result.horizon if result.horizon is not None else ""),
            "duration_seconds": str(result.duration_seconds),
            "result": json.dumps(payload),
            "finished_at": str(time.time()),
        })
        await redis.expire(key, _JOB_KEY_TTL_S)


def _opt_int(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _truthy(raw) -> bool:
    if raw is None:
        return False
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _split_extra(raw) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return [s for s in str(raw).split() if s]
