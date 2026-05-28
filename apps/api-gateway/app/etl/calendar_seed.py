"""Seed/refresh `dim_calendar` with Indonesian feature flags.

Generates one row per day in [start, end] populating:
- Date parts (day_of_week, week_of_year, month, quarter, is_month_start/end, is_weekend)
- Indonesian holiday windows (ramadan, lebaran ±, nataru, idul adha, school holiday, harvest)

Usage:
  python -m app.etl.calendar_seed --start 2022-01-01 --end 2026-12-31
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


# Idul Fitri day-1 (1 Syawal) — Indonesian government observed.
LEBARAN_DAY1: dict[int, date] = {
    2020: date(2020, 5, 24),
    2021: date(2021, 5, 13),
    2022: date(2022, 5, 2),
    2023: date(2023, 4, 22),
    2024: date(2024, 4, 10),
    2025: date(2025, 3, 31),
    2026: date(2026, 3, 20),
    2027: date(2027, 3, 9),
    2028: date(2028, 2, 26),
    2029: date(2029, 2, 14),
    2030: date(2030, 2, 4),
}

# 1 Ramadan (first day of fasting).
RAMADAN_START: dict[int, date] = {
    2020: date(2020, 4, 24),
    2021: date(2021, 4, 13),
    2022: date(2022, 4, 2),
    2023: date(2023, 3, 23),
    2024: date(2024, 3, 11),
    2025: date(2025, 3, 1),
    2026: date(2026, 2, 18),
    2027: date(2027, 2, 8),
    2028: date(2028, 1, 28),
    2029: date(2029, 1, 16),
    2030: date(2030, 1, 5),
}

# Idul Adha (10 Dhulhijjah).
IDUL_ADHA: dict[int, date] = {
    2020: date(2020, 7, 31),
    2021: date(2021, 7, 20),
    2022: date(2022, 7, 10),
    2023: date(2023, 6, 29),
    2024: date(2024, 6, 17),
    2025: date(2025, 6, 6),
    2026: date(2026, 5, 27),
    2027: date(2027, 5, 17),
    2028: date(2028, 5, 5),
    2029: date(2029, 4, 24),
    2030: date(2030, 4, 13),
}


def _compute_flags(d: date) -> dict:
    y = d.year
    lebaran = LEBARAN_DAY1.get(y)
    lebaran_prev = LEBARAN_DAY1.get(y - 1)
    lebaran_next = LEBARAN_DAY1.get(y + 1)
    ramadan = RAMADAN_START.get(y)
    ramadan_prev = RAMADAN_START.get(y - 1)
    idul_adha = IDUL_ADHA.get(y)

    def _in_ramadan() -> bool:
        for rs, le in [(ramadan, lebaran), (ramadan_prev, LEBARAN_DAY1.get(y - 1))]:
            if rs and le and rs <= d < le:
                return True
        return False

    def _delta(target: date | None) -> int | None:
        return (d - target).days if target else None

    flags = {
        "ramadan_flag": _in_ramadan(),
        "lebaran_minus_21": any(_delta(le) == -21 for le in (lebaran, lebaran_next) if le),
        "lebaran_minus_14": any(_delta(le) == -14 for le in (lebaran, lebaran_next) if le),
        "lebaran_minus_7": any(-7 <= (_delta(le) or 99) <= -1 for le in (lebaran, lebaran_next) if le),
        "lebaran_plus_7": any(0 <= (_delta(le) or -99) <= 7 for le in (lebaran, lebaran_prev) if le),
        "nataru_minus_14": (d.month == 12 and 11 <= d.day <= 24),
        "idul_adha_window": idul_adha is not None and abs((d - idul_adha).days) <= 3,
        # School holidays: late Dec / first week Jan, mid-Jun → mid-Jul.
        "school_holiday_flag": (
            (d.month == 12 and d.day >= 20)
            or (d.month == 1 and d.day <= 5)
            or (d.month == 6 and d.day >= 20)
            or (d.month == 7 and d.day <= 15)
        ),
        # Main rice harvest seasons (gadu Feb-May, rendengan Oct-Dec).
        "harvest_flag": d.month in (2, 3, 4, 5, 10, 11, 12),
    }
    return flags


def _is_national_holiday(d: date) -> tuple[bool, str | None]:
    # Static national holidays (non-Islamic — Islamic ones handled via Lebaran/Idul Adha windows).
    fixed = {
        (1, 1): "Tahun Baru",
        (5, 1): "Hari Buruh",
        (6, 1): "Hari Lahir Pancasila",
        (8, 17): "HUT Kemerdekaan RI",
        (12, 25): "Hari Raya Natal",
    }
    name = fixed.get((d.month, d.day))
    if name:
        return True, name
    if LEBARAN_DAY1.get(d.year) and d in (LEBARAN_DAY1[d.year], LEBARAN_DAY1[d.year] + timedelta(days=1)):
        return True, "Idul Fitri"
    if IDUL_ADHA.get(d.year) == d:
        return True, "Idul Adha"
    return False, None


def _season(d: date) -> str:
    # Indonesian climatology: rainy (Nov-Apr), dry (May-Oct).
    return "musim_hujan" if d.month in (11, 12, 1, 2, 3, 4) else "musim_kemarau"


def _row(d: date) -> dict:
    flags = _compute_flags(d)
    is_libur, nama_libur = _is_national_holiday(d)
    return {
        "tanggal": d,
        "tahun": d.year,
        "bulan": d.month,
        "minggu_ke": int(d.strftime("%V")),
        "hari_ke": d.timetuple().tm_yday,
        "nama_hari": d.strftime("%A"),
        "is_weekend": d.weekday() >= 5,
        "is_hari_libur": is_libur,
        "nama_libur": nama_libur,
        "musim": _season(d),
        "day_of_week": d.weekday(),
        "week_of_year": int(d.strftime("%V")),
        "quarter": (d.month - 1) // 3 + 1,
        "is_month_start": d.day == 1,
        "is_month_end": (d + timedelta(days=1)).month != d.month,
        **flags,
    }


_UPSERT_SQL = text("""
INSERT INTO dim_calendar (
    tanggal, tahun, bulan, minggu_ke, hari_ke, nama_hari, is_weekend,
    is_hari_libur, nama_libur, musim, day_of_week, week_of_year, quarter,
    is_month_start, is_month_end, ramadan_flag, lebaran_minus_21, lebaran_minus_14,
    lebaran_minus_7, lebaran_plus_7, nataru_minus_14, idul_adha_window,
    school_holiday_flag, harvest_flag
) VALUES (
    :tanggal, :tahun, :bulan, :minggu_ke, :hari_ke, :nama_hari, :is_weekend,
    :is_hari_libur, :nama_libur, :musim, :day_of_week, :week_of_year, :quarter,
    :is_month_start, :is_month_end, :ramadan_flag, :lebaran_minus_21, :lebaran_minus_14,
    :lebaran_minus_7, :lebaran_plus_7, :nataru_minus_14, :idul_adha_window,
    :school_holiday_flag, :harvest_flag
)
ON CONFLICT (tanggal) DO UPDATE SET
    tahun = EXCLUDED.tahun,
    bulan = EXCLUDED.bulan,
    minggu_ke = EXCLUDED.minggu_ke,
    hari_ke = EXCLUDED.hari_ke,
    nama_hari = EXCLUDED.nama_hari,
    is_weekend = EXCLUDED.is_weekend,
    is_hari_libur = EXCLUDED.is_hari_libur,
    nama_libur = EXCLUDED.nama_libur,
    musim = EXCLUDED.musim,
    day_of_week = EXCLUDED.day_of_week,
    week_of_year = EXCLUDED.week_of_year,
    quarter = EXCLUDED.quarter,
    is_month_start = EXCLUDED.is_month_start,
    is_month_end = EXCLUDED.is_month_end,
    ramadan_flag = EXCLUDED.ramadan_flag,
    lebaran_minus_21 = EXCLUDED.lebaran_minus_21,
    lebaran_minus_14 = EXCLUDED.lebaran_minus_14,
    lebaran_minus_7 = EXCLUDED.lebaran_minus_7,
    lebaran_plus_7 = EXCLUDED.lebaran_plus_7,
    nataru_minus_14 = EXCLUDED.nataru_minus_14,
    idul_adha_window = EXCLUDED.idul_adha_window,
    school_holiday_flag = EXCLUDED.school_holiday_flag,
    harvest_flag = EXCLUDED.harvest_flag
""")


async def seed(db: AsyncSession, start: date, end: date) -> int:
    if end < start:
        raise ValueError("end must be >= start")
    count = 0
    cur = start
    batch: list[dict] = []
    while cur <= end:
        batch.append(_row(cur))
        if len(batch) >= 200:
            await db.execute(_UPSERT_SQL, batch)
            count += len(batch)
            batch.clear()
        cur += timedelta(days=1)
    if batch:
        await db.execute(_UPSERT_SQL, batch)
        count += len(batch)
    await db.commit()
    return count


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Seed dim_calendar with ML feature flags")
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--end", required=True, type=date.fromisoformat)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    engine = create_async_engine(_resolve_url(), pool_recycle=300)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        n = await seed(db, args.start, args.end)
    await engine.dispose()
    logger.info("Seeded %s calendar rows from %s to %s", n, args.start, args.end)


if __name__ == "__main__":
    # When run as script (not -m), make sure project root is importable.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    asyncio.run(_main())
