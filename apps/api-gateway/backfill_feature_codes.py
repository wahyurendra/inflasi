"""One-off: populate the new *_code columns on existing feature_store_daily rows.

Migration 0005 added 10 nullable columns. The standard ``FeatureBuilder`` would
fill them, but it reads from ``fact_price_daily`` which doesn't cover the
historical window the feature store was seeded from. So we compute the codes
directly from the identity columns already present and UPDATE in place — same
encoder, identical results.

Run once after migration 0005. Idempotent (UPDATE; re-running produces same
values).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.services.feature_encoder import (  # noqa: E402
    ENTITY_LEVEL_CODES, FREQUENCY_CODES, SERIES_FAMILY_CODES, UNIT_CODES,
    _hash32, _hash64,
)

logger = logging.getLogger("backfill_feature_codes")


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL", "")
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    engine = create_async_engine(_resolve_url(), pool_pre_ping=True)

    async with engine.connect() as conn:
        # 1. Per-group code UPDATE — one statement per distinct identity tuple.
        groups = (await conn.execute(text(
            """
            SELECT DISTINCT commodity_id, region_id, entity_id,
                   entity_level, frequency, series_family, unit
            FROM feature_store_daily
            """
        ))).fetchall()
        logger.info("encoding %s distinct identity groups", len(groups))

        for i, g in enumerate(groups, 1):
            commodity_id = g.commodity_id
            region_id = g.region_id
            entity_id = g.entity_id
            entity_level = g.entity_level or ""
            frequency = g.frequency or "daily"
            series_family = g.series_family or ""
            unit = g.unit or ""

            params = {
                "commodity_id": commodity_id,
                "region_id": region_id,
                "entity_id": entity_id,
                "entity_level": entity_level,
                "frequency": frequency,
                "series_family": series_family,
                "unit": unit,
                "commodity_id_code": _hash32(commodity_id),
                "region_id_code": _hash32(region_id),
                "entity_id_code": _hash32(entity_id) if entity_id else _hash32(region_id),
                "entity_level_code": ENTITY_LEVEL_CODES.get(entity_level, 0),
                "frequency_code": FREQUENCY_CODES.get(frequency, 0),
                "series_family_code": SERIES_FAMILY_CODES.get(series_family, 0),
                "unit_code": UNIT_CODES.get(unit, 0),
                "series_key_code": _hash64(f"{commodity_id}|{region_id}|{entity_level}"),
            }
            await conn.execute(text(
                """
                UPDATE feature_store_daily
                SET commodity_id_code  = :commodity_id_code,
                    region_id_code     = :region_id_code,
                    entity_id_code     = :entity_id_code,
                    entity_level_code  = :entity_level_code,
                    frequency_code     = :frequency_code,
                    series_family_code = :series_family_code,
                    unit_code          = :unit_code,
                    series_key_code    = :series_key_code
                WHERE commodity_id   = :commodity_id
                  AND region_id      = :region_id
                  AND entity_level   = :entity_level
                """
            ), params)
            if i % 50 == 0:
                logger.info("  %s / %s groups done", i, len(groups))

        # 2. has_complete_* — single UPDATE, computed from existing weather/macro cols.
        result = await conn.execute(text(
            """
            UPDATE feature_store_daily
            SET has_complete_weather = CASE
                  WHEN rainfall_1d IS NOT NULL AND temperature_avg IS NOT NULL THEN 1
                  ELSE 0
                END,
                has_complete_macro = CASE
                  WHEN usd_idr_change IS NOT NULL AND inflation_mom_lag_1 IS NOT NULL THEN 1
                  ELSE 0
                END
            """
        ))
        logger.info("has_complete_* updated (%s rows)", result.rowcount)

        await conn.commit()

    await engine.dispose()
    logger.info("done")


if __name__ == "__main__":
    asyncio.run(main())
