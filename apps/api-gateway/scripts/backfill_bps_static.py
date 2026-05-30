"""Backfill `fact_inflation_monthly` from BPS static tables.

The dynamic API (used by the original `bps_inflation` pipeline) is
Cloudflare-fronted, so we fetch the published static XLS tables instead.

Tables loaded:

* **tid=913** — Inflasi Bulanan (M-to-M) Nasional → `inflasi_mtm`
* **tid=915** — Inflasi Tahunan (Y-on-Y) Nasional → `inflasi_yoy`
* **tid=914** — Inflasi Y-to-D Nasional → `inflasi_ytd`

Wide format (rows = months Januari..Desember, columns = years). We pivot back
to long and upsert one row per (period, region_id, kelompok='umum').

Provincial breakdown is **not** included — BPS publishes per-province tables
under different IDs; add them later by extending `TABLES`.

Requires `cloudscraper` + `xlrd` (legacy XLS format).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date

import cloudscraper
import xlrd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("backfill_bps_static")

BPS_BASE = "https://webapi.bps.go.id/v1/api"

# (table_id, target column in fact_inflation_monthly)
TABLES: list[tuple[int, str]] = [
    (913, "inflasi_mtm"),
    (915, "inflasi_yoy"),
    (914, "inflasi_ytd"),
]

INDO_MONTHS: dict[str, int] = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11,
    "desember": 12,
}


def _scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "darwin", "desktop": True},
    )


def fetch_excel(scraper, table_id: int, api_key: str) -> bytes | None:
    """Resolve the static table's signed download URL, then fetch the bytes."""
    view_url = (
        f"{BPS_BASE}/view/domain/0000/model/statictable/lang/ind/"
        f"id/{table_id}/key/{api_key}/"
    )
    resp = scraper.get(view_url, timeout=30)
    payload = resp.json()
    data = payload.get("data") or {}
    excel_url = data.get("excel")
    if not excel_url:
        logger.warning("no excel URL for table %s: %s", table_id, payload)
        return None
    r = scraper.get(excel_url, timeout=60)
    if r.status_code != 200 or not r.content:
        logger.warning("download failed table=%s status=%s", table_id, r.status_code)
        return None
    return r.content


def parse_wide_table(content: bytes) -> list[tuple[date, float]]:
    """Pivot a (row=month, col=year) wide sheet to `[(period, value)]`."""
    wb = xlrd.open_workbook(file_contents=content)
    sheet = wb.sheets()[0]

    # Find the header row (contains "Bulan" + numeric years).
    header_row: int | None = None
    year_columns: list[tuple[int, int]] = []  # (col_index, year)
    for ri in range(min(sheet.nrows, 10)):
        row = sheet.row_values(ri)
        if not row:
            continue
        cell0 = str(row[0]).strip().lower()
        if cell0 != "bulan":
            continue
        for ci, cell in enumerate(row[1:], start=1):
            try:
                year = int(float(str(cell).strip()))
                if 1990 < year < 2100:
                    year_columns.append((ci, year))
            except (TypeError, ValueError):
                continue
        if year_columns:
            header_row = ri
            break

    if header_row is None or not year_columns:
        return []

    out: list[tuple[date, float]] = []
    for ri in range(header_row + 1, sheet.nrows):
        row = sheet.row_values(ri)
        if not row:
            continue
        month_label = str(row[0]).strip().lower()
        month_num = INDO_MONTHS.get(month_label)
        if month_num is None:
            continue
        for col_idx, year in year_columns:
            if col_idx >= len(row):
                continue
            cell = row[col_idx]
            if cell in (None, "", "-"):
                continue
            try:
                value = float(cell)
            except (TypeError, ValueError):
                continue
            out.append((date(year, month_num, 1), value))
    return out


async def upsert(
    db: AsyncSession,
    *,
    region_id: int,
    column: str,
    rows: list[tuple[date, float]],
    level_wilayah: str = "nasional",
) -> int:
    if not rows:
        return 0
    sql = text(f"""
        INSERT INTO fact_inflation_monthly
          (periode, region_id, level_wilayah, kelompok, {column}, sumber)
        VALUES (:periode, :region_id, :level_wilayah, 'umum', :value, 'BPS')
        ON CONFLICT (periode, region_id, kelompok, commodity_id)
        DO UPDATE SET
          {column} = EXCLUDED.{column},
          updated_at = NOW()
    """)
    params = [
        {
            "periode": d, "region_id": region_id,
            "level_wilayah": level_wilayah, "value": v,
        }
        for d, v in rows
    ]
    await db.execute(sql, params)
    await db.commit()
    return len(params)


async def _resolve_national_region(db: AsyncSession) -> int | None:
    """Look up the row representing the national rollup."""
    r = (await db.execute(
        text("SELECT id FROM dim_region WHERE kode_wilayah = :kode"),
        {"kode": "nasional"},
    )).scalar()
    if r:
        return int(r)
    r = (await db.execute(
        text("SELECT id FROM dim_region WHERE level_wilayah = 'nasional' LIMIT 1"),
    )).scalar()
    return int(r) if r else None


async def run(*, api_key: str) -> dict[str, int]:
    summary: dict[str, int] = {}
    scraper = _scraper()
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as db:
            region_id = await _resolve_national_region(db)
            if region_id is None:
                logger.error("no 'nasional' row in dim_region; seed dimensions first")
                return {}
            for table_id, column in TABLES:
                content = fetch_excel(scraper, table_id, api_key)
                if not content:
                    summary[column] = 0
                    continue
                rows = parse_wide_table(content)
                written = await upsert(
                    db, region_id=region_id, column=column, rows=rows,
                )
                summary[column] = written
                logger.info("table=%s column=%s wrote=%s", table_id, column, written)
    finally:
        await engine.dispose()
    return summary


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Backfill BPS national inflation via static tables.")
    parser.add_argument("--api-key", default=None,
                        help="Overrides BPS_API_KEY env var.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    api_key = args.api_key or os.getenv("BPS_API_KEY")
    if not api_key:
        raise SystemExit("BPS_API_KEY env var (or --api-key) required")
    summary = asyncio.run(run(api_key=api_key))
    logger.info("backfill summary: %s", summary)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
