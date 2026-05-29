"""Seed dimension tables — runs once on a fresh database.

Three dimensions are populated here:

* `dim_region` — 34 BPS provinces + national rollup (35 rows). The BPS code is
  the unique key; lat/lon are seeded from province capital cities so the
  geospatial dashboard works out of the box without a follow-up backfill.
* `dim_commodity` — the eight MVP commodities the rest of the stack expects.
  Codes must match `app/etl/mappings/commodity_map.py`.
* `badges` — gamification defaults so first-run users see real challenges.

`dim_calendar` is handled separately by `app/etl/calendar_seed.py` because the
calendar generator is reused by analytics ad-hoc reruns.

All seeds are idempotent via `ON CONFLICT DO UPDATE`. Re-running picks up any
field tweaks (renames, lat/lon corrections) without duplicating rows.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Sequence

import cuid2
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("seed_dimensions")


# ── Region ───────────────────────────────────────────────────
# (kode_wilayah, nama_provinsi, nama_kab_kota, level_wilayah, latitude, longitude)
# lat/lon = provincial capital so the dashboard map can pin markers from row 0.
REGIONS: Sequence[tuple[str, str, str | None, str, float | None, float | None]] = (
    ("00", "Indonesia", None, "nasional", -2.5489, 118.0149),
    ("11", "Aceh", None, "provinsi", 5.5483, 95.3238),
    ("12", "Sumatera Utara", None, "provinsi", 3.5952, 98.6722),
    ("13", "Sumatera Barat", None, "provinsi", -0.9492, 100.3543),
    ("14", "Riau", None, "provinsi", 0.5071, 101.4478),
    ("15", "Jambi", None, "provinsi", -1.6101, 103.6131),
    ("16", "Sumatera Selatan", None, "provinsi", -2.9909, 104.7566),
    ("17", "Bengkulu", None, "provinsi", -3.7928, 102.2608),
    ("18", "Lampung", None, "provinsi", -5.4500, 105.2667),
    ("19", "Kepulauan Bangka Belitung", None, "provinsi", -2.1410, 106.1147),
    ("21", "Kepulauan Riau", None, "provinsi", 1.0838, 104.0273),
    ("31", "DKI Jakarta", None, "provinsi", -6.2088, 106.8456),
    ("32", "Jawa Barat", None, "provinsi", -6.9175, 107.6191),
    ("33", "Jawa Tengah", None, "provinsi", -6.9667, 110.4167),
    ("34", "DI Yogyakarta", None, "provinsi", -7.7956, 110.3695),
    ("35", "Jawa Timur", None, "provinsi", -7.2575, 112.7521),
    ("36", "Banten", None, "provinsi", -6.1200, 106.1503),
    ("51", "Bali", None, "provinsi", -8.6500, 115.2167),
    ("52", "Nusa Tenggara Barat", None, "provinsi", -8.5833, 116.1167),
    ("53", "Nusa Tenggara Timur", None, "provinsi", -10.1772, 123.6070),
    ("61", "Kalimantan Barat", None, "provinsi", -0.0263, 109.3425),
    ("62", "Kalimantan Tengah", None, "provinsi", -2.2089, 113.9134),
    ("63", "Kalimantan Selatan", None, "provinsi", -3.3194, 114.5908),
    ("64", "Kalimantan Timur", None, "provinsi", -0.5022, 117.1536),
    ("65", "Kalimantan Utara", None, "provinsi", 2.8333, 117.3833),
    ("71", "Sulawesi Utara", None, "provinsi", 1.4748, 124.8421),
    ("72", "Sulawesi Tengah", None, "provinsi", -0.9003, 119.8779),
    ("73", "Sulawesi Selatan", None, "provinsi", -5.1477, 119.4327),
    ("74", "Sulawesi Tenggara", None, "provinsi", -3.9985, 122.5127),
    ("75", "Gorontalo", None, "provinsi", 0.5435, 123.0568),
    ("76", "Sulawesi Barat", None, "provinsi", -2.6713, 118.8889),
    ("81", "Maluku", None, "provinsi", -3.6555, 128.1908),
    ("82", "Maluku Utara", None, "provinsi", 0.7843, 127.3789),
    ("91", "Papua", None, "provinsi", -2.5337, 140.7181),
    ("92", "Papua Barat", None, "provinsi", -0.8615, 134.0620),
)


# ── Commodity ────────────────────────────────────────────────
# (kode, nama, nama_display, kategori, satuan, is_strategis, is_mvp)
COMMODITIES: Sequence[tuple[str, str, str, str, str, bool, bool]] = (
    ("BERAS",         "Beras",          "Beras Medium",       "pangan_pokok",   "kg",    True, True),
    ("CABAI_MERAH",   "Cabai Merah",    "Cabai Merah Besar",  "sayuran",        "kg",    True, True),
    ("CABAI_RAWIT",   "Cabai Rawit",    "Cabai Rawit Merah",  "sayuran",        "kg",    True, True),
    ("BAWANG_MERAH",  "Bawang Merah",   "Bawang Merah",       "sayuran",        "kg",    True, True),
    ("BAWANG_PUTIH",  "Bawang Putih",   "Bawang Putih",       "sayuran",        "kg",    True, True),
    ("TELUR_AYAM",    "Telur Ayam Ras", "Telur Ayam",         "protein_hewani", "kg",    True, True),
    ("MINYAK_GORENG", "Minyak Goreng",  "Minyak Goreng Curah", "minyak",        "liter", True, True),
    ("GULA_PASIR",    "Gula Pasir",     "Gula Pasir Lokal",   "pangan_pokok",   "kg",    True, True),
)


# ── Badges ───────────────────────────────────────────────────
# (code, name, description, icon, threshold, category)
BADGES: Sequence[tuple[str, str, str, str, int, str]] = (
    ("first_report",    "Pelapor Pemula",      "Laporan pertama dikirim",        "seedling",  1,   "milestone"),
    ("reporter_10",     "Pelapor Aktif",        "10 laporan disetujui",           "trophy",    10,  "milestone"),
    ("reporter_50",     "Pelapor Handal",       "50 laporan disetujui",           "medal",     50,  "milestone"),
    ("reporter_100",    "Pelapor Expert",       "100 laporan disetujui",          "crown",     100, "milestone"),
    ("streak_7",        "Konsisten 7 Hari",     "Laporan 7 hari berturut-turut",  "flame",     7,   "streak"),
    ("streak_30",       "Konsisten 30 Hari",    "Laporan 30 hari berturut-turut", "star",      30,  "streak"),
    ("multi_commodity", "Multi Komoditas",       "Laporan 5+ komoditas berbeda",   "target",    5,   "diversity"),
    ("multi_region",    "Multi Wilayah",         "Laporan dari 3+ wilayah",        "map",       3,   "diversity"),
)


# ── Upsert SQL ───────────────────────────────────────────────

_UPSERT_REGION = text("""
    INSERT INTO dim_region
      (kode_wilayah, nama_provinsi, nama_kab_kota, level_wilayah, latitude, longitude, is_active)
    VALUES (:kode_wilayah, :nama_provinsi, :nama_kab_kota, :level_wilayah, :latitude, :longitude, TRUE)
    ON CONFLICT (kode_wilayah) DO UPDATE SET
      nama_provinsi = EXCLUDED.nama_provinsi,
      nama_kab_kota = EXCLUDED.nama_kab_kota,
      level_wilayah = EXCLUDED.level_wilayah,
      latitude = EXCLUDED.latitude,
      longitude = EXCLUDED.longitude,
      is_active = TRUE
""")

_UPSERT_COMMODITY = text("""
    INSERT INTO dim_commodity
      (kode_komoditas, nama_komoditas, nama_display, kategori, satuan, is_strategis, is_mvp)
    VALUES (:kode, :nama, :nama_display, :kategori, :satuan, :is_strategis, :is_mvp)
    ON CONFLICT (kode_komoditas) DO UPDATE SET
      nama_komoditas = EXCLUDED.nama_komoditas,
      nama_display = EXCLUDED.nama_display,
      kategori = EXCLUDED.kategori,
      satuan = EXCLUDED.satuan,
      is_strategis = EXCLUDED.is_strategis,
      is_mvp = EXCLUDED.is_mvp
""")

_UPSERT_BADGE = text("""
    INSERT INTO badges (id, code, name, description, icon, threshold, category)
    VALUES (:id, :code, :name, :description, :icon, :threshold, :category)
    ON CONFLICT (code) DO UPDATE SET
      name = EXCLUDED.name,
      description = EXCLUDED.description,
      icon = EXCLUDED.icon,
      threshold = EXCLUDED.threshold,
      category = EXCLUDED.category
""")


# ── Driver ───────────────────────────────────────────────────

async def seed_regions(db: AsyncSession) -> int:
    rows = [
        {
            "kode_wilayah": k, "nama_provinsi": n, "nama_kab_kota": kk,
            "level_wilayah": lv, "latitude": lat, "longitude": lon,
        }
        for (k, n, kk, lv, lat, lon) in REGIONS
    ]
    await db.execute(_UPSERT_REGION, rows)
    return len(rows)


async def seed_commodities(db: AsyncSession) -> int:
    rows = [
        {
            "kode": kode, "nama": nama, "nama_display": nd,
            "kategori": kat, "satuan": sat,
            "is_strategis": strat, "is_mvp": mvp,
        }
        for (kode, nama, nd, kat, sat, strat, mvp) in COMMODITIES
    ]
    await db.execute(_UPSERT_COMMODITY, rows)
    return len(rows)


async def seed_badges(db: AsyncSession) -> int:
    rows = [
        {
            "id": cuid2.cuid_wrapper()(),
            "code": code, "name": name, "description": desc,
            "icon": icon, "threshold": threshold, "category": cat,
        }
        for (code, name, desc, icon, threshold, cat) in BADGES
    ]
    await db.execute(_UPSERT_BADGE, rows)
    return len(rows)


async def main(*, include: set[str]) -> dict[str, int]:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    summary: dict[str, int] = {}
    async with factory() as db:
        if "regions" in include:
            summary["regions"] = await seed_regions(db)
        if "commodities" in include:
            summary["commodities"] = await seed_commodities(db)
        if "badges" in include:
            summary["badges"] = await seed_badges(db)
        await db.commit()
    await engine.dispose()
    return summary


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Seed dim_region, dim_commodity, badges.")
    parser.add_argument(
        "--skip", action="append", default=[],
        choices=["regions", "commodities", "badges"],
        help="Skip a specific dimension (repeatable).",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    include = {"regions", "commodities", "badges"} - set(args.skip)
    summary = asyncio.run(main(include=include))
    logger.info("seed_dimensions summary: %s", summary)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
