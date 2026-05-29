"""One-time backfill of `fact_inflation_monthly` from BPS Web API.

Same pipeline as the nightly job (`app.etl.pipelines.bps_inflation`), just
invoked with explicit year bounds and chunked region-by-region so a failure
on one province doesn't take the whole backfill down with it.

Usage:
    python -m scripts.backfill_bps_inflation \\
        --start-year 2022 --end-year 2026
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.etl.pipelines.bps_inflation import BPS_DOMAIN_MAP, BPSInflationPipeline

logger = logging.getLogger("backfill_bps_inflation")


async def run(
    *,
    start_year: int,
    end_year: int,
    api_key: str | None = None,
    region_codes: list[str] | None = None,
    per_call_delay_s: float = 0.5,
) -> dict[str, int]:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    summary: dict[str, int] = {}
    regions = region_codes or sorted(BPS_DOMAIN_MAP.keys())
    try:
        async with factory() as db:
            for region_code in regions:
                pipeline = BPSInflationPipeline(
                    db=db,
                    api_key=api_key,
                    start_year=start_year,
                    end_year=end_year,
                    region_codes=[region_code],
                    per_call_delay_s=per_call_delay_s,
                )
                try:
                    written = await pipeline.run()
                except Exception:
                    logger.exception("region=%s failed; continuing", region_code)
                    written = 0
                summary[region_code] = written
                logger.info("region=%s rows=%s", region_code, written)
    finally:
        await engine.dispose()
    return summary


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    today = date.today()
    parser = argparse.ArgumentParser(description="Backfill BPS inflation monthly.")
    parser.add_argument("--start-year", type=int, default=2022)
    parser.add_argument("--end-year", type=int, default=today.year)
    parser.add_argument("--api-key", default=None, help="Overrides BPS_API_KEY env var.")
    parser.add_argument("--regions", default=None,
                        help="Comma-separated dim_region.kode_wilayah values; default = all.")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Seconds between BPS API calls (be a good citizen).")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    region_codes = (
        [c.strip() for c in args.regions.split(",") if c.strip()]
        if args.regions else None
    )

    summary = asyncio.run(run(
        start_year=args.start_year,
        end_year=args.end_year,
        api_key=args.api_key,
        region_codes=region_codes,
        per_call_delay_s=args.delay,
    ))
    total = sum(summary.values())
    logger.info("backfill complete: %s rows across %s regions", total, len(summary))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
