"""One-time backfill: seed `dim_market` from existing `price_reports.nama_pasar`.

For each (region_id, nama_pasar) that appears at least `--min-reports` times in
the past `--days`, we either reuse an existing `dim_market` row or insert one.
Then we update every matching `price_reports` row to point at that market via
the fuzzy normalizer.

Idempotent — safe to re-run. The normalizer caches per region, so the per-row
update step is cheap even on large datasets.

Usage:
    python -m scripts.backfill_markets --days 365 --min-reports 3
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import select, text

from app.database import async_session
from app.db.repositories.market_repo import MarketRepo
from app.etl.pipelines.market_normalizer import MarketNormalizer
from app.models.tables import PriceReport

logger = logging.getLogger("backfill_markets")


async def backfill(*, days: int, min_reports: int, dry_run: bool) -> dict:
    cutoff = date.today() - timedelta(days=days)
    seeded = 0
    matched_reports = 0
    skipped_reports = 0

    async with async_session() as db:
        rows = (await db.execute(
            text("""
                SELECT region_id, nama_pasar, COUNT(*) AS n
                FROM price_reports
                WHERE tanggal >= :cutoff AND nama_pasar IS NOT NULL
                GROUP BY region_id, nama_pasar
                HAVING COUNT(*) >= :min_reports
                ORDER BY n DESC
            """),
            {"cutoff": cutoff, "min_reports": min_reports},
        )).fetchall()

        repo = MarketRepo(db)
        for row in rows:
            region_id = int(row.region_id)
            name = row.nama_pasar
            existing = await repo.find_by_region_name(
                region_id=region_id, nama_pasar=name,
            )
            if existing is None and not dry_run:
                await repo.upsert(region_id=region_id, nama_pasar=name)
                seeded += 1
            elif existing is None:
                seeded += 1
        if not dry_run:
            await db.commit()

    async with async_session() as db:
        normalizer = MarketNormalizer(db)
        # Stream price_reports needing assignment in batches.
        result = await db.execute(
            select(PriceReport).where(
                PriceReport.market_id.is_(None),
                PriceReport.tanggal >= cutoff,
            )
        )
        for report in result.scalars().all():
            try:
                match = await normalizer.resolve(
                    region_id=report.region_id,
                    nama_pasar=report.nama_pasar,
                    auto_create=False,
                )
            except Exception:
                logger.exception("normalize failed for report %s", report.id)
                skipped_reports += 1
                continue
            if match is None:
                skipped_reports += 1
                continue
            if not dry_run:
                report.market_id = match.market_id
            matched_reports += 1
        if not dry_run:
            await db.commit()

    return {
        "candidates": len(rows),
        "seeded_markets": seeded,
        "matched_reports": matched_reports,
        "skipped_reports": skipped_reports,
        "dry_run": dry_run,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="Backfill dim_market from price_reports.")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--min-reports", type=int, default=3,
                        help="Minimum reports per (region, name) to seed a market.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    summary = asyncio.run(backfill(
        days=args.days, min_reports=args.min_reports, dry_run=args.dry_run,
    ))
    logger.info("backfill summary: %s", summary)


if __name__ == "__main__":
    _main()
