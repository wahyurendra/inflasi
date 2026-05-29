"""Comprehensive data-quality check after init / backfill.

Runs every "did this work?" SQL we usually copy-paste into psql when something
feels off. Targets are loosely matched to the plan's expectations (see
`INFLASI_Real_Data_Init_Plan.md §13`); a row prints as `PASS` only when the
metric clears its target, otherwise `WARN` or `FAIL` with the observed value.

Exit code: 0 if no FAIL rows, 1 otherwise. WARN doesn't trigger non-zero so
the script stays usable from CI smoke-tests during the early-data phase when
coverage is naturally low.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("verify_data")


@dataclass
class Check:
    name: str
    actual: Any
    target: str
    status: str  # "PASS" | "WARN" | "FAIL"

    def render(self) -> str:
        return f"  [{self.status:4}] {self.name:42} actual={self.actual!s:<18} target={self.target}"


async def _scalar(db: AsyncSession, sql: str, params: dict | None = None) -> Any:
    return (await db.execute(text(sql), params or {})).scalar()


async def _row(db: AsyncSession, sql: str, params: dict | None = None) -> Any:
    return (await db.execute(text(sql), params or {})).first()


def _grade(actual: int | float, target_min: int | float, *, warn_floor: int | float | None = None) -> str:
    if actual >= target_min:
        return "PASS"
    if warn_floor is not None and actual >= warn_floor:
        return "WARN"
    return "FAIL"


async def run() -> int:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    checks: list[Check] = []

    try:
        async with factory() as db:
            checks.extend(await _check_dimensions(db))
            checks.extend(await _check_facts(db))
            checks.extend(await _check_feature_store(db))
            checks.extend(await _check_models(db))
    finally:
        await engine.dispose()

    print("─" * 96)
    print(f"  INFLASI Data Verification")
    print("─" * 96)
    for c in checks:
        print(c.render())
    failed = [c for c in checks if c.status == "FAIL"]
    warned = [c for c in checks if c.status == "WARN"]
    print("─" * 96)
    print(f"  Summary: {len(checks)} checks   "
          f"PASS={len(checks) - len(failed) - len(warned)}   "
          f"WARN={len(warned)}   FAIL={len(failed)}")
    return 1 if failed else 0


async def _check_dimensions(db: AsyncSession) -> list[Check]:
    out: list[Check] = []
    regions = await _scalar(db, "SELECT count(*) FROM dim_region")
    commodities = await _scalar(db, "SELECT count(*) FROM dim_commodity")
    calendar = await _scalar(db, "SELECT count(*) FROM dim_calendar")
    badges = await _scalar(db, "SELECT count(*) FROM badges")

    out.append(Check("dim_region rows", regions, ">= 35",
                     _grade(int(regions or 0), 35, warn_floor=30)))
    out.append(Check("dim_commodity rows", commodities, ">= 8",
                     _grade(int(commodities or 0), 8, warn_floor=4)))
    out.append(Check("dim_calendar rows", calendar, ">= 1825",  # ~5 years
                     _grade(int(calendar or 0), 1825, warn_floor=365)))
    out.append(Check("badges rows", badges, ">= 8",
                     _grade(int(badges or 0), 8, warn_floor=4)))
    return out


async def _check_facts(db: AsyncSession) -> list[Check]:
    out: list[Check] = []
    tables = [
        ("fact_price_daily", "tanggal", 50_000, 5_000),
        ("fact_inflation_monthly", "periode", 500, 50),
        ("fact_climate", "tanggal", 5_000, 500),
        ("fact_macro_driver", "tanggal", 365, 30),
    ]
    for table, time_col, target, warn in tables:
        row = await _row(
            db,
            f"SELECT count(*) AS n, max({time_col})::text AS latest FROM {table}",
        )
        n = int(row.n) if row and row.n else 0
        latest = row.latest if row else None
        out.append(Check(
            f"{table} rows", n, f">= {target}",
            _grade(n, target, warn_floor=warn),
        ))
        out.append(Check(
            f"{table} latest {time_col}", latest, "not null",
            "PASS" if latest else "WARN",
        ))

    # External signals — softer thresholds, mostly liveness.
    ext_tables = [
        "ext_exchange_rate", "ext_energy_price",
        "ext_commodity_price", "ext_fao_food_price", "ext_supply_chain_index",
    ]
    for t in ext_tables:
        n = int(await _scalar(db, f"SELECT count(*) FROM {t}") or 0)
        out.append(Check(f"{t} rows", n, ">= 100",
                         _grade(n, 100, warn_floor=10)))
    return out


async def _check_feature_store(db: AsyncSession) -> list[Check]:
    out: list[Check] = []
    n = int(await _scalar(db, "SELECT count(*) FROM feature_store_daily") or 0)
    out.append(Check("feature_store_daily rows", n, ">= 100000",
                     _grade(n, 100_000, warn_floor=5_000)))
    if n == 0:
        return out

    row = await _row(
        db,
        """
        SELECT
            count(*) AS total,
            count(price_lag_7) AS lag7,
            count(rolling_mean_30) AS roll30,
            count(target_h7) AS target_h7,
            count(rainfall_1d) AS weather,
            count(usd_idr_change) AS macro
        FROM feature_store_daily
        """,
    )
    if row is None:
        return out
    total = int(row.total)

    def pct(num: int) -> float:
        return round(100 * num / total, 1) if total else 0.0

    for label, attr, target_pct in (
        ("price_lag_7 coverage", "lag7", 95.0),
        ("rolling_mean_30 coverage", "roll30", 90.0),
        ("target_h7 coverage", "target_h7", 90.0),
        ("rainfall_1d coverage", "weather", 60.0),
        ("usd_idr_change coverage", "macro", 80.0),
    ):
        val = pct(int(getattr(row, attr) or 0))
        out.append(Check(
            label, f"{val}%", f">= {target_pct}%",
            _grade(val, target_pct, warn_floor=target_pct * 0.5),
        ))

    # Splits
    split_row = await _row(
        db,
        """
        SELECT
            sum(CASE WHEN split = 'train' THEN 1 ELSE 0 END) AS train,
            sum(CASE WHEN split = 'validation' THEN 1 ELSE 0 END) AS val,
            sum(CASE WHEN split = 'test' THEN 1 ELSE 0 END) AS test
        FROM feature_store_daily
        """,
    )
    if split_row is not None:
        out.append(Check("train split rows", int(split_row.train or 0),
                         ">= 50000", _grade(int(split_row.train or 0), 50_000, warn_floor=1_000)))
        out.append(Check("validation split rows", int(split_row.val or 0),
                         ">= 5000", _grade(int(split_row.val or 0), 5_000, warn_floor=100)))
        out.append(Check("test split rows", int(split_row.test or 0),
                         ">= 5000", _grade(int(split_row.test or 0), 5_000, warn_floor=100)))
    return out


async def _check_models(db: AsyncSession) -> list[Check]:
    out: list[Check] = []
    active = int(await _scalar(
        db, "SELECT count(*) FROM model_registry WHERE is_active = true",
    ) or 0)
    out.append(Check("active models", active, ">= 1",
                     _grade(active, 1, warn_floor=0)))

    forecasts_today = int(await _scalar(
        db,
        "SELECT count(*) FROM analytics_forecast WHERE created_at >= now() - INTERVAL '24 hours'",
    ) or 0)
    out.append(Check("forecasts written last 24h", forecasts_today, ">= 200",
                     _grade(forecasts_today, 200, warn_floor=10)))

    runs = int(await _scalar(db, "SELECT count(*) FROM model_training_runs") or 0)
    out.append(Check("training runs recorded", runs, ">= 1",
                     _grade(runs, 1, warn_floor=0)))
    return out


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Data quality verification.")
    parser.add_argument("--log-level", default="WARNING")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
