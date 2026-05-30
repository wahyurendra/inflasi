"""Backfill `fact_climate` with historical weather from Open-Meteo.

BMKG's public API only serves forecasts. For multi-year historical coverage
(needed to compute `rainfall_anomaly` etc.) we use Open-Meteo's free archive,
which exposes daily aggregates without an API key.

API: https://open-meteo.com/en/docs/historical-weather-api

For each province we pin a representative lat/lon (the provincial capital
seeded by `seed_dimensions.py`), pull daily totals, and upsert into
`fact_climate`. The endpoint accepts a multi-year range in one request so a
single province usually takes one HTTP call.

Usage:
    python -m scripts.backfill_weather_openmeteo \\
        --start 2022-01-01 --end 2026-05-29
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("backfill_weather_openmeteo")

OPENMETEO_URL = "https://archive-api.open-meteo.com/v1/archive"

# Daily variables we want from Open-Meteo. Names map directly into
# `fact_climate` via `_normalize_row`.
DAILY_VARS = ",".join((
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "wind_speed_10m_max",
))

_CONCURRENCY = 4  # Open-Meteo is generous but we still cap politely.


async def fetch_region(
    client: httpx.AsyncClient,
    *,
    latitude: float,
    longitude: float,
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": DAILY_VARS,
        "timezone": "Asia/Jakarta",
    }
    resp = await client.get(OPENMETEO_URL, params=params)
    resp.raise_for_status()
    return _flatten(resp.json())


def _flatten(payload: dict[str, Any]) -> list[dict[str, Any]]:
    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    rows: list[dict[str, Any]] = []
    for i, tstr in enumerate(times):
        try:
            t = date.fromisoformat(tstr)
        except (TypeError, ValueError):
            continue
        rows.append({
            "tanggal": t,
            "temperature_2m_mean": _pick(daily, "temperature_2m_mean", i),
            "precipitation_sum": _pick(daily, "precipitation_sum", i),
            "rain_sum": _pick(daily, "rain_sum", i),
            "wind_speed_10m_max": _pick(daily, "wind_speed_10m_max", i),
        })
    return rows


def _pick(daily: dict[str, Any], key: str, i: int) -> float | None:
    arr = daily.get(key)
    if not isinstance(arr, list) or i >= len(arr):
        return None
    v = arr[i]
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


async def _upsert(
    db: AsyncSession,
    *,
    region_id: int,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0
    params = [
        {
            "tanggal": r["tanggal"],
            "region_id": region_id,
            "curah_hujan": r.get("precipitation_sum") or r.get("rain_sum"),
            "suhu_rata": r.get("temperature_2m_mean"),
            "anomali_cuaca": _label_anomaly(r),
            "warning_level": _warning_level(r),
        }
        for r in rows
    ]
    await db.execute(
        text("""
            INSERT INTO fact_climate
              (tanggal, region_id, curah_hujan, suhu_rata, anomali_cuaca, warning_level, sumber)
            VALUES
              (:tanggal, :region_id, :curah_hujan, :suhu_rata, :anomali_cuaca, :warning_level, 'OPEN_METEO')
            ON CONFLICT (tanggal, region_id) DO UPDATE SET
              curah_hujan = COALESCE(EXCLUDED.curah_hujan, fact_climate.curah_hujan),
              suhu_rata = COALESCE(EXCLUDED.suhu_rata, fact_climate.suhu_rata),
              anomali_cuaca = EXCLUDED.anomali_cuaca,
              warning_level = EXCLUDED.warning_level
        """),
        params,
    )
    await db.commit()
    return len(params)


def _label_anomaly(row: dict[str, Any]) -> str | None:
    rain = row.get("precipitation_sum") or row.get("rain_sum") or 0
    if rain >= 100:
        return "hujan ekstrim"
    if rain >= 50:
        return "hujan lebat"
    if rain == 0:
        return "tidak hujan"
    return None


def _warning_level(row: dict[str, Any]) -> str | None:
    rain = row.get("precipitation_sum") or row.get("rain_sum") or 0
    wind = row.get("wind_speed_10m_max") or 0
    if rain >= 100 or wind >= 50:
        return "AWAS"
    if rain >= 50 or wind >= 35:
        return "SIAGA"
    if rain >= 20 or wind >= 20:
        return "WASPADA"
    return None


async def _list_regions(db: AsyncSession) -> list[tuple[int, str, float, float]]:
    rows = (await db.execute(
        text("""
            SELECT id, kode_wilayah, latitude, longitude
            FROM dim_region
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND level_wilayah <> 'nasional'
            ORDER BY kode_wilayah
        """),
    )).fetchall()
    return [
        (int(r.id), r.kode_wilayah, float(r.latitude), float(r.longitude))
        for r in rows
    ]


async def run(*, start: date, end: date, region_codes: list[str] | None = None) -> dict[str, int]:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300, pool_size=8, max_overflow=4)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    summary: dict[str, int] = {}
    sem = asyncio.Semaphore(_CONCURRENCY)
    try:
        async with factory() as db:
            regions = await _list_regions(db)
        if region_codes:
            wanted = set(region_codes)
            regions = [r for r in regions if r[1] in wanted]
        if not regions:
            logger.warning("no regions found; seed dimensions first")
            return {}

        async with httpx.AsyncClient(timeout=60.0) as client:
            async def _one(region: tuple[int, str, float, float]) -> None:
                # One fresh session per region — sharing a single AsyncSession
                # serializes upserts across all 35 regions, which on hypertables
                # collapses throughput to a couple of regions per hour.
                region_id, code, lat, lon = region
                async with sem:
                    try:
                        rows = await fetch_region(
                            client, latitude=lat, longitude=lon,
                            start=start, end=end,
                        )
                    except Exception:
                        logger.exception("fetch failed: region=%s", code)
                        summary[code] = 0
                        return
                try:
                    async with factory() as db_local:
                        n = await _upsert(db_local, region_id=region_id, rows=rows)
                    summary[code] = n
                    logger.info("region=%s rows=%s", code, n)
                except Exception:
                    logger.exception("upsert failed: region=%s", code)
                    summary[code] = 0

            await asyncio.gather(*(_one(r) for r in regions))
    finally:
        await engine.dispose()
    return summary


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Backfill fact_climate from Open-Meteo archive.")
    parser.add_argument("--start", default="2022-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--regions", default=None,
                        help="Comma-separated dim_region.kode_wilayah values; default = all provinces.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else date.today()
    region_codes = (
        [c.strip() for c in args.regions.split(",") if c.strip()]
        if args.regions else None
    )
    summary = asyncio.run(run(start=start, end=end, region_codes=region_codes))
    total = sum(summary.values())
    logger.info("backfill complete: %s rows across %s regions", total, len(summary))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
