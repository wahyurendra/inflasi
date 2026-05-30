"""Seed `dim_commodity` and `dim_region` with the canonical INFLASI universe.

The `kode_komoditas` / `kode_wilayah` slugs match what appears in
`feature_store_daily` so existing 492k+ feature rows align with the dim ids
after this runs. Idempotent (`ON CONFLICT DO NOTHING`).

Usage:
  python -m app.etl.dim_seed
"""

from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


# (kode_komoditas, nama_komoditas, nama_display, kategori, satuan, is_strategis, is_mvp)
COMMODITIES: list[tuple[str, str, str, str, str, bool, bool]] = [
    ("beras",                 "Beras Premium",        "Beras",              "pangan_pokok", "kg", True,  True),
    ("bawang_merah",          "Bawang Merah",         "Bawang Merah",       "bumbu",        "kg", True,  True),
    ("bawang_putih",          "Bawang Putih",         "Bawang Putih",       "bumbu",        "kg", True,  True),
    ("cabai_merah",           "Cabai Merah Keriting", "Cabai Merah",        "bumbu",        "kg", True,  True),
    ("cabai_rawit",           "Cabai Rawit Merah",    "Cabai Rawit",        "bumbu",        "kg", True,  True),
    ("daging_ayam",           "Daging Ayam Ras",      "Daging Ayam",        "protein",      "kg", True,  True),
    ("daging_sapi",           "Daging Sapi Murni",    "Daging Sapi",        "protein",      "kg", True,  True),
    ("telur_ayam",            "Telur Ayam Ras",       "Telur Ayam",         "protein",      "kg", True,  True),
    ("gula_pasir",            "Gula Pasir Lokal",     "Gula Pasir",         "pangan_pokok", "kg", True,  True),
    ("tepung_terigu_curah",   "Tepung Terigu Curah",  "Tepung Terigu",      "pangan_pokok", "kg", True,  True),
]


# (kode_wilayah, nama_provinsi, level_wilayah, latitude, longitude)
# Coordinates approximate ibukota provinsi. `nasional` aggregate for nation-wide queries.
REGIONS: list[tuple[str, str, str, float | None, float | None]] = [
    ("nasional",                  "Nasional",                "nasional", None,      None),
    ("aceh",                      "Aceh",                    "provinsi", 5.5483,    95.3238),
    ("sumatera_utara",            "Sumatera Utara",          "provinsi", 3.5952,    98.6722),
    ("sumatera_barat",            "Sumatera Barat",          "provinsi", -0.9492,   100.3543),
    ("riau",                      "Riau",                    "provinsi", 0.5071,    101.4478),
    ("kepulauan_riau",            "Kepulauan Riau",          "provinsi", 1.0668,    104.0344),
    ("jambi",                     "Jambi",                   "provinsi", -1.6101,   103.6131),
    ("sumatera_selatan",          "Sumatera Selatan",        "provinsi", -2.9909,   104.7566),
    ("kepulauan_bangka_belitung", "Kepulauan Bangka Belitung","provinsi",-2.1410,   106.1130),
    ("bengkulu",                  "Bengkulu",                "provinsi", -3.7928,   102.2608),
    ("lampung",                   "Lampung",                 "provinsi", -5.4500,   105.2667),
    ("dki_jakarta",               "DKI Jakarta",             "provinsi", -6.2088,   106.8456),
    ("banten",                    "Banten",                  "provinsi", -6.1200,   106.1503),
    ("jawa_barat",                "Jawa Barat",              "provinsi", -6.9175,   107.6191),
    ("jawa_tengah",               "Jawa Tengah",             "provinsi", -6.9667,   110.4167),
    ("di_yogyakarta",             "DI Yogyakarta",           "provinsi", -7.7956,   110.3695),
    ("jawa_timur",                "Jawa Timur",              "provinsi", -7.2575,   112.7521),
    ("bali",                      "Bali",                    "provinsi", -8.6500,   115.2167),
    ("nusa_tenggara_barat",       "Nusa Tenggara Barat",     "provinsi", -8.5833,   116.1167),
    ("nusa_tenggara_timur",       "Nusa Tenggara Timur",     "provinsi", -10.1772,  123.6070),
    ("kalimantan_barat",          "Kalimantan Barat",        "provinsi", -0.0263,   109.3425),
    ("kalimantan_tengah",         "Kalimantan Tengah",       "provinsi", -2.2088,   113.9163),
    ("kalimantan_selatan",        "Kalimantan Selatan",      "provinsi", -3.3194,   114.5908),
    ("kalimantan_timur",          "Kalimantan Timur",        "provinsi", -0.5022,   117.1536),
    ("kalimantan_utara",          "Kalimantan Utara",        "provinsi", 2.8500,    117.3667),
    ("sulawesi_utara",            "Sulawesi Utara",          "provinsi", 1.4748,    124.8421),
    ("gorontalo",                 "Gorontalo",               "provinsi", 0.5435,    123.0568),
    ("sulawesi_tengah",           "Sulawesi Tengah",         "provinsi", -0.8917,   119.8707),
    ("sulawesi_barat",            "Sulawesi Barat",          "provinsi", -2.6885,   118.8907),
    ("sulawesi_selatan",          "Sulawesi Selatan",        "provinsi", -5.1477,   119.4327),
    ("sulawesi_tenggara",         "Sulawesi Tenggara",       "provinsi", -3.9985,   122.5128),
    ("maluku",                    "Maluku",                  "provinsi", -3.6954,   128.1814),
    ("maluku_utara",              "Maluku Utara",            "provinsi", 0.7833,    127.3833),
    ("papua_barat",               "Papua Barat",             "provinsi", -0.8615,   134.0620),
    ("papua",                     "Papua",                   "provinsi", -2.5337,   140.7181),
]


_UPSERT_COMMODITY = text("""
    INSERT INTO dim_commodity
        (kode_komoditas, nama_komoditas, nama_display, kategori, satuan, is_strategis, is_mvp)
    VALUES
        (:kode, :nama, :display, :kategori, :satuan, :strategis, :mvp)
    ON CONFLICT (kode_komoditas) DO NOTHING
""")

_UPSERT_REGION = text("""
    INSERT INTO dim_region
        (kode_wilayah, nama_provinsi, level_wilayah, latitude, longitude, is_active)
    VALUES
        (:kode, :nama, :level, :lat, :lon, TRUE)
    ON CONFLICT (kode_wilayah) DO NOTHING
""")


async def seed() -> dict[str, int]:
    url = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not url:
        url = "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"

    engine = create_async_engine(url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    counts: dict[str, int] = {}
    async with session_factory() as session:
        for c in COMMODITIES:
            await session.execute(_UPSERT_COMMODITY, {
                "kode": c[0], "nama": c[1], "display": c[2],
                "kategori": c[3], "satuan": c[4],
                "strategis": c[5], "mvp": c[6],
            })
        for r in REGIONS:
            await session.execute(_UPSERT_REGION, {
                "kode": r[0], "nama": r[1], "level": r[2],
                "lat": r[3], "lon": r[4],
            })
        await session.commit()

        for tbl in ("dim_commodity", "dim_region"):
            row = (await session.execute(text(f"SELECT count(*) FROM {tbl}"))).scalar()
            counts[tbl] = row or 0

    await engine.dispose()
    return counts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    counts = asyncio.run(seed())
    for k, v in counts.items():
        logger.info("%s: %s rows", k, v)


if __name__ == "__main__":
    main()
