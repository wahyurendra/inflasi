"""Materialize `feature_store_daily` rows.

Usage:
  python run_feature_build.py                                  # today
  python run_feature_build.py 2026-05-28                       # specific date
  python run_feature_build.py --backfill 2022-01-01 2026-05-28 # range
  python run_feature_build.py --lookback 90                    # lookback window
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

_project_root = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(_project_root, ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Build feature_store_daily rows")
    parser.add_argument("target", nargs="?", type=date.fromisoformat,
                        help="Target date (YYYY-MM-DD); defaults to today")
    parser.add_argument("--backfill", nargs=2, metavar=("START", "END"),
                        help="Backfill range [START, END] inclusive")
    parser.add_argument("--lookback", type=int, default=60,
                        help="Days of price history needed for lags/rolling (default 60)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    from app.services.feature_builder import FeatureBuilder

    engine = create_async_engine(_resolve_url(), pool_recycle=300, echo=args.verbose)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        builder = FeatureBuilder(db)
        if args.backfill:
            start = date.fromisoformat(args.backfill[0])
            end = date.fromisoformat(args.backfill[1])
            print(f"\n  Feature backfill {start} → {end}")
            n = await builder.backfill(start, end)
        else:
            target = args.target or date.today()
            print(f"\n  Feature build for {target} (lookback={args.lookback})")
            n = await builder.build(target, lookback_days=args.lookback)
        print(f"  ✓ {n} feature rows materialized\n")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
