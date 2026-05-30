"""Seed BI Rate + retail fuel prices into `fact_macro_driver`.

Both indicators change rarely — BI Rate moves a handful of times per year at
the monthly RDG, and government fuel prices step on policy events. Scraping
them is overkill and error-prone, so we just hard-code the observed history
and forward-fill into a daily series.

The forward-fill is what makes this a "seed" rather than a "rate sheet": once
written, every day from the first BI Rate change through `--end-date` has a
non-null `kurs_usd_idr` slot? — no, those come from the kurs pipeline. The
columns we set are:

* `harga_bbm`  ← retail Pertalite (RON 90) price (Rp / liter)
* `kurs_usd_idr` is **left untouched** because the kurs pipeline owns it.

BI Rate is recorded as a separate `bi_rate` column once that column exists.
For now we store it in a JSONB stash under `params` of the most recent change
event (left as TODO until the schema supports it natively).

Idempotent. Run once per environment.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date, timedelta
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("seed_macro_manual")


# ── BBM (Pertalite RON 90) — Pertamina retail (region-flat for MVP) ────
# (effective_from, price_idr_per_liter)
# Sourced from Pertamina announcements. Mid-period revisions can be appended
# safely; the script forward-fills.
FUEL_PRICE_HISTORY: Sequence[tuple[date, int]] = (
    (date(2022, 1, 1), 7650),    # carry-over from 2021 schedule
    (date(2022, 9, 3), 10000),   # September 2022 hike
    (date(2023, 1, 3), 10000),
    (date(2023, 6, 1), 10000),
    (date(2024, 1, 1), 10000),
    (date(2024, 10, 1), 10000),
    (date(2025, 1, 1), 10000),
    (date(2025, 7, 1), 10000),
    (date(2026, 1, 1), 10000),
    (date(2026, 4, 1), 12000),   # placeholder; update when policy moves
)


# ── BI Rate — RDG decisions (BI 7-Day Reverse Repo) ───────────────────
# (effective_from, bi_rate_pct)
BI_RATE_HISTORY: Sequence[tuple[date, float]] = (
    (date(2022, 1, 1), 3.50),
    (date(2022, 8, 23), 3.75),
    (date(2022, 9, 22), 4.25),
    (date(2022, 10, 20), 4.75),
    (date(2022, 11, 17), 5.25),
    (date(2023, 1, 19), 5.75),
    (date(2024, 4, 24), 6.25),
    (date(2024, 9, 18), 6.00),
    (date(2025, 1, 15), 5.75),
    (date(2026, 1, 15), 5.50),
)


async def seed(
    db: AsyncSession,
    *,
    start: date,
    end: date,
    overwrite: bool = False,
) -> int:
    """Forward-fill BBM (and best-effort BI Rate) into `fact_macro_driver`.

    Strategy: for every day in `[start, end]`, pick the most recent rate at or
    before that date from each history table. Insert (or skip) into
    `fact_macro_driver`. The kurs columns are deliberately left as-is.
    """
    rows: list[dict] = []
    cur = start
    while cur <= end:
        fuel = _step(cur, FUEL_PRICE_HISTORY)
        bi = _step(cur, BI_RATE_HISTORY)
        if fuel is None and bi is None:
            cur += timedelta(days=1)
            continue
        rows.append({
            "tanggal": cur,
            "harga_bbm": fuel,
            "bi_rate": bi,  # stored for completeness; consumed via params below
        })
        cur += timedelta(days=1)

    if not rows:
        logger.info("nothing to seed in window %s..%s", start, end)
        return 0

    written = 0
    set_clause = (
        "harga_bbm = EXCLUDED.harga_bbm"
        if overwrite
        else "harga_bbm = COALESCE(fact_macro_driver.harga_bbm, EXCLUDED.harga_bbm)"
    )
    for row in rows:
        await db.execute(
            text(f"""
                INSERT INTO fact_macro_driver
                  (tanggal, harga_bbm, sumber_kurs)
                VALUES (:tanggal, :harga_bbm, 'BI_JISDOR')
                ON CONFLICT (tanggal)
                DO UPDATE SET {set_clause}
            """),
            {"tanggal": row["tanggal"], "harga_bbm": row["harga_bbm"]},
        )
        written += 1
    await db.commit()

    # BI Rate has no dedicated column in `fact_macro_driver` today. Surface it
    # as an `analytics_insights` row so the operator can see what's been seeded
    # — replace this once the schema gains a `bi_rate` field natively.
    # Note: asyncpg doesn't auto-encode dict → jsonb via raw text(), so we cast
    # explicitly with `::jsonb` and pass a JSON-encoded string.
    import json

    latest_bi = max((r["tanggal"], r["bi_rate"]) for r in rows if r["bi_rate"] is not None)
    snapshot = json.dumps({
        "history": [
            {"date": d.isoformat(), "bi_rate": r} for d, r in BI_RATE_HISTORY
        ],
    })
    await db.execute(
        text("""
            INSERT INTO analytics_insights (tanggal, tipe, judul, konten, data_snapshot)
            VALUES (:tanggal, 'macro_seed', 'BI Rate seed (manual)',
                    :konten, CAST(:snapshot AS JSONB))
            ON CONFLICT DO NOTHING
        """),
        {
            "tanggal": latest_bi[0],
            "konten": f"BI Rate per {latest_bi[0].isoformat()} = {latest_bi[1]}%",
            "snapshot": snapshot,
        },
    )
    await db.commit()

    logger.info("seeded %s macro rows; latest BI rate=%s %%", written, latest_bi[1])
    return written


def _step(d: date, history: Sequence[tuple[date, float | int]]):
    """Most-recent value at or before `d`. None if `d` precedes the first row."""
    chosen = None
    for effective_from, value in history:
        if effective_from <= d:
            chosen = value
        else:
            break
    return chosen


async def main(*, start: date, end: date, overwrite: bool) -> int:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as db:
            return await seed(db, start=start, end=end, overwrite=overwrite)
    finally:
        await engine.dispose()


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Seed BBM + BI Rate into fact_macro_driver.")
    parser.add_argument("--start", default="2022-01-01", help="YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD (defaults to today)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing harga_bbm values instead of leaving them.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else date.today()
    rows = asyncio.run(main(start=start, end=end, overwrite=args.overwrite))
    logger.info("done: %s rows", rows)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
