"""Bulk load PIHPS BI price data from local CSV files.

Use this when the live PIHPS API is rate-limiting or down and you have a stash
of historical CSV exports — either scraped, downloaded from BI's bulk export,
or shared by another team. The expected CSV shape matches the fallback path
already supported by `app/etl/pipelines/pihps_bi.py`:

    tanggal,wilayah,komoditas,harga
    2024-01-02,DKI Jakarta,Beras Medium,14500
    2024-01-02,Jawa Barat,Cabai Merah Besar,38000

Names are normalized via `app/etl/mappings/region_map` and `commodity_map`, so
case and minor variants are forgiven. Rows that don't normalize are skipped
with a warning and counted in the summary.

Two execution styles:

    # 1. One file at a time
    python -m scripts.bulk_load_pihps --file ./data/pihps_2024-01-02.csv

    # 2. A whole directory of files matching pihps_*.csv
    python -m scripts.bulk_load_pihps --dir ./data/pihps_archive/

Idempotent: uses ON CONFLICT DO UPDATE so re-running overwrites the existing
crowd / official value for that (date, region, commodity).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.etl.mappings.commodity_map import normalize_commodity
from app.etl.mappings.region_map import normalize_region

logger = logging.getLogger("bulk_load_pihps")


@dataclass
class LoadSummary:
    files: int
    raw_rows: int
    written: int
    skipped_region: int
    skipped_commodity: int
    skipped_price: int


def _iter_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k.strip().lower(): (v or "").strip() for k, v in row.items()}


def _files_from_args(file_arg: str | None, dir_arg: str | None) -> list[Path]:
    if file_arg and dir_arg:
        raise SystemExit("specify --file or --dir, not both")
    if file_arg:
        p = Path(file_arg)
        if not p.exists():
            raise SystemExit(f"file not found: {p}")
        return [p]
    if dir_arg:
        d = Path(dir_arg)
        if not d.exists() or not d.is_dir():
            raise SystemExit(f"directory not found: {d}")
        files = sorted(d.glob("pihps_*.csv"))
        if not files:
            raise SystemExit(f"no pihps_*.csv files found under {d}")
        return files
    raise SystemExit("specify --file or --dir")


async def _id_maps(db: AsyncSession) -> tuple[dict[str, int], dict[str, int]]:
    rgn = (await db.execute(text("SELECT id, kode_wilayah FROM dim_region"))).fetchall()
    cmd = (await db.execute(text("SELECT id, kode_komoditas FROM dim_commodity"))).fetchall()
    return (
        {r.kode_wilayah: int(r.id) for r in rgn},
        {r.kode_komoditas: int(r.id) for r in cmd},
    )


async def load_files(
    files: list[Path],
    *,
    sumber: str = "PIHPS_BI",
) -> LoadSummary:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    summary = LoadSummary(
        files=0, raw_rows=0, written=0,
        skipped_region=0, skipped_commodity=0, skipped_price=0,
    )

    try:
        async with factory() as db:
            region_ids, commodity_ids = await _id_maps(db)
            if not region_ids or not commodity_ids:
                raise SystemExit("dim_region / dim_commodity empty; seed dimensions first")

            for path in files:
                summary.files += 1
                logger.info("loading %s", path)
                batch: list[dict] = []
                for raw in _iter_csv_rows(path):
                    summary.raw_rows += 1
                    parsed = _parse_row(raw, region_ids, commodity_ids, summary)
                    if parsed is None:
                        continue
                    batch.append({**parsed, "sumber": sumber})

                if not batch:
                    logger.warning("no usable rows in %s", path.name)
                    continue
                await _upsert(db, batch)
                summary.written += len(batch)
                logger.info("wrote %s rows from %s", len(batch), path.name)
    finally:
        await engine.dispose()
    return summary


def _parse_row(
    raw: dict[str, str],
    region_ids: dict[str, int],
    commodity_ids: dict[str, int],
    summary: LoadSummary,
) -> dict | None:
    try:
        tanggal = date.fromisoformat(raw.get("tanggal", "")[:10])
    except (TypeError, ValueError):
        return None

    region_code = normalize_region(raw.get("wilayah", ""))
    if region_code is None or region_code not in region_ids:
        summary.skipped_region += 1
        return None

    commodity_code = normalize_commodity(raw.get("komoditas", ""))
    if commodity_code is None or commodity_code not in commodity_ids:
        summary.skipped_commodity += 1
        return None

    try:
        harga = float(str(raw.get("harga", "")).replace(",", ""))
    except (TypeError, ValueError):
        summary.skipped_price += 1
        return None
    if not (100 <= harga <= 500_000):
        summary.skipped_price += 1
        return None

    return {
        "tanggal": tanggal,
        "region_id": region_ids[region_code],
        "commodity_id": commodity_ids[commodity_code],
        "harga": harga,
    }


async def _upsert(db: AsyncSession, rows: list[dict]) -> None:
    await db.execute(
        text("""
            INSERT INTO fact_price_daily
              (tanggal, region_id, commodity_id, harga, sumber)
            VALUES (:tanggal, :region_id, :commodity_id, :harga, :sumber)
            ON CONFLICT (tanggal, region_id, commodity_id)
            DO UPDATE SET harga = EXCLUDED.harga, sumber = EXCLUDED.sumber
        """),
        rows,
    )
    await db.commit()


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Bulk-load PIHPS CSV exports.")
    parser.add_argument("--file", default=None, help="Single CSV file")
    parser.add_argument("--dir", default=None, help="Directory containing pihps_*.csv files")
    parser.add_argument("--sumber", default="PIHPS_BI",
                        help="Value written to fact_price_daily.sumber")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    files = _files_from_args(args.file, args.dir)
    summary = asyncio.run(load_files(files, sumber=args.sumber))
    logger.info(
        "bulk_load_pihps done: files=%s raw=%s written=%s "
        "skipped_region=%s skipped_commodity=%s skipped_price=%s",
        summary.files, summary.raw_rows, summary.written,
        summary.skipped_region, summary.skipped_commodity, summary.skipped_price,
    )


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
