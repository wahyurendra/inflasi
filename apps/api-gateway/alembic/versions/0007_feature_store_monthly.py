"""feature_store_monthly — supervised dataset for inflation forecasting

Mirrors the daily feature store but with monthly grain (period = first day of
the month). The schema covers:

* **CPI core** — ihk, inflasi_mtm/yoy/ytd, lags 1/3/6/12, rolling 3/6
* **Food-price proxy** — aggregated mean/median/anomaly from fact_price_daily,
  plus per-commodity month-over-month change for the strategic commodities
  (beras, cabai merah, bawang merah, telur, ayam, minyak goreng)
* **Weather / macro** — monthly rainfall anomaly, kurs change, BBM change
* **Calendar / events** — month, quarter, ramadan/lebaran/idul_adha flags
* **Targets** — inflation at M+1, M+3, M+6 (computed in the builder, never
  read at inference time)
* **Quality / split** — `data_quality_score`, `split` (train/val/test)

Idempotent: CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS.

Revision ID: 0007_feature_store_monthly
Revises: 0006_market_dimension
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0007_feature_store_monthly"
down_revision: Union[str, None] = "0006_market_dimension"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS feature_store_monthly (
            id BIGSERIAL PRIMARY KEY,
            period DATE NOT NULL,
            region_id INTEGER NOT NULL REFERENCES dim_region(id),
            target_type VARCHAR(50) NOT NULL DEFAULT 'inflation',
            level_wilayah VARCHAR(20),

            -- CPI core
            ihk NUMERIC(10,2),
            inflasi_mtm NUMERIC(8,4),
            inflasi_yoy NUMERIC(8,4),
            inflasi_ytd NUMERIC(8,4),

            -- Lags
            inflasi_lag_1 NUMERIC(8,4),
            inflasi_lag_3 NUMERIC(8,4),
            inflasi_lag_6 NUMERIC(8,4),
            inflasi_lag_12 NUMERIC(8,4),

            -- Rolling
            inflasi_rolling_3 NUMERIC(8,4),
            inflasi_rolling_6 NUMERIC(8,4),
            inflasi_std_3 NUMERIC(8,4),
            inflasi_std_6 NUMERIC(8,4),

            -- Food-price proxy aggregates (from fact_price_daily)
            food_price_index NUMERIC(12,4),
            food_price_change_mom NUMERIC(8,4),
            food_price_anomaly NUMERIC(8,4),

            -- Per-commodity MoM (strategic six)
            beras_change_mom NUMERIC(8,4),
            cabai_merah_change_mom NUMERIC(8,4),
            bawang_merah_change_mom NUMERIC(8,4),
            telur_change_mom NUMERIC(8,4),
            ayam_change_mom NUMERIC(8,4),
            minyak_goreng_change_mom NUMERIC(8,4),

            -- Weather (monthly mean / anomaly)
            rainfall_mean NUMERIC(10,4),
            rainfall_anomaly NUMERIC(8,4),
            temperature_mean NUMERIC(6,2),
            extreme_weather_days INTEGER,

            -- Macro
            kurs_usd_idr NUMERIC(12,2),
            kurs_change_mom NUMERIC(8,4),
            bbm_price NUMERIC(10,2),
            bbm_change_mom NUMERIC(8,4),

            -- Calendar / event flags
            month INTEGER,
            quarter INTEGER,
            ramadan_flag INTEGER,
            lebaran_flag INTEGER,
            idul_adha_flag INTEGER,
            nataru_flag INTEGER,
            harvest_flag INTEGER,

            -- Targets (M+1, M+3, M+6 future inflation)
            target_inflation_m1 NUMERIC(8,4),
            target_inflation_m3 NUMERIC(8,4),
            target_inflation_m6 NUMERIC(8,4),

            -- Quality + split
            data_quality_score NUMERIC(6,4),
            split VARCHAR(20),

            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (period, region_id, target_type)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fsm_period "
        "ON feature_store_monthly (period DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fsm_region_period "
        "ON feature_store_monthly (region_id, period DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fsm_split "
        "ON feature_store_monthly (split, period)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_fsm_split")
    op.execute("DROP INDEX IF EXISTS idx_fsm_region_period")
    op.execute("DROP INDEX IF EXISTS idx_fsm_period")
    op.execute("DROP TABLE IF EXISTS feature_store_monthly")
