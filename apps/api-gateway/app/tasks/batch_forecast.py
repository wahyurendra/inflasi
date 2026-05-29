"""Batch forecast orchestrator — runs the full prediction pipeline for every
active (commodity, region) pair across the requested horizons.

Designed to run two ways:

* **CronJob** — `python -m app.tasks.batch_forecast --horizon 7,14,30`. K8s
  invokes this nightly after the analytics ETL settles. Exits 0 on partial
  success; the per-pair error log is the source of truth.
* **In-process** — `await run_batch_forecast(...)` from the `forecast_batch_worker`
  Redis-Streams consumer. Same code path; the worker decides when.

Bounded concurrency through an asyncio.Semaphore over the ml-gateway calls,
because that is the rate-limited dependency. Per-pair errors are captured into
`BatchError` records so a single bad pair never blocks the rest of the run.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from dataclasses import asdict, dataclass

from app.database import async_session
from app.services.prediction_service import DEFAULT_HORIZONS, PredictionService
from app.tasks.batch_utils import BatchError, discover_active_pairs

logger = logging.getLogger("batch_forecast")

_DEFAULT_CONCURRENCY = 4


@dataclass
class BatchForecastResult:
    """Aggregate summary of a batch run. Returned to the caller (worker, CLI,
    admin endpoint) and is JSON-friendly via `asdict`."""
    pairs_total: int
    pairs_succeeded: int
    pairs_failed: int
    points_written: int
    horizons: list[int]
    duration_seconds: float
    errors: list[dict]


async def run_batch_forecast(
    *,
    horizons: list[int] | None = None,
    pair_limit: int | None = None,
    concurrency: int = _DEFAULT_CONCURRENCY,
    window_days: int = 7,
) -> BatchForecastResult:
    """Execute one batch run end-to-end.

    `horizons` defaults to `PredictionService.DEFAULT_HORIZONS`. `pair_limit`
    caps the total pairs processed (useful for smoke tests). `window_days`
    controls how recent a pair must be to qualify as "active".
    """
    horizons = sorted(set(horizons or list(DEFAULT_HORIZONS)))
    start = time.monotonic()

    async with async_session() as db:
        pairs = await discover_active_pairs(db, window_days=window_days)

    if pair_limit is not None:
        pairs = pairs[:pair_limit]

    logger.info(
        "batch_forecast start: pairs=%s horizons=%s concurrency=%s",
        len(pairs), horizons, concurrency,
    )

    sem = asyncio.Semaphore(concurrency)
    succeeded = 0
    failed = 0
    points_written = 0
    errors: list[BatchError] = []

    async def _one(pair: tuple[int, int]) -> None:
        nonlocal succeeded, failed, points_written
        cid, rid = pair
        async with sem:
            try:
                async with async_session() as db:
                    service = PredictionService(db)
                    pts = await service.forecast_pair_all_horizons(
                        commodity_id=cid, region_id=rid,
                    )
                    await db.commit()
                points_written += len(pts)
                succeeded += 1
            except Exception as exc:
                failed += 1
                errors.append(BatchError(
                    commodity_id=cid, region_id=rid, horizon=None,
                    error=f"{type(exc).__name__}: {exc}",
                ))
                logger.exception("batch_forecast pair failed: c=%s r=%s", cid, rid)

    await asyncio.gather(*(_one(p) for p in pairs))

    duration = time.monotonic() - start
    result = BatchForecastResult(
        pairs_total=len(pairs),
        pairs_succeeded=succeeded,
        pairs_failed=failed,
        points_written=points_written,
        horizons=horizons,
        duration_seconds=round(duration, 2),
        errors=[asdict(e) for e in errors[:50]],  # cap to keep the payload bounded
    )
    logger.info(
        "batch_forecast done: success=%s failed=%s points=%s duration=%.1fs",
        succeeded, failed, points_written, duration,
    )
    return result


def _parse_horizons(raw: str) -> list[int]:
    return [int(x) for x in raw.split(",") if x.strip()]


def _main() -> None:
    parser = argparse.ArgumentParser(description="Run batch forecast across active pairs.")
    parser.add_argument("--horizon", default="7,14,30", help="Comma-separated horizons.")
    parser.add_argument("--limit", type=int, default=None, help="Cap pairs processed.")
    parser.add_argument("--concurrency", type=int, default=_DEFAULT_CONCURRENCY)
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    result = asyncio.run(run_batch_forecast(
        horizons=_parse_horizons(args.horizon),
        pair_limit=args.limit,
        concurrency=args.concurrency,
        window_days=args.window_days,
    ))
    # Exit non-zero only when everything failed — partial success is normal.
    raise SystemExit(0 if result.pairs_succeeded or result.pairs_total == 0 else 1)


if __name__ == "__main__":
    _main()
