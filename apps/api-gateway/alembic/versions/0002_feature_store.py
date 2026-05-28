"""feature_store_daily — wide ML feature table

Mirrors `unified_ready_dataset` CSV one-to-one: lags, rolling stats, calendar
flags, weather, macro, and supervised targets (h7/h14/h30).

Revision ID: 0002_feature_store
Revises: 0001_baseline
Create Date: 2026-05-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_feature_store"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_store_daily",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("commodity_id", sa.String(50), nullable=False),
        sa.Column("region_id", sa.String(50), nullable=False),
        sa.Column("entity_level", sa.String(20), nullable=False),
        sa.Column("series_family", sa.String(50), nullable=False),
        sa.Column("split", sa.String(20)),
        sa.Column("row_role", sa.String(50)),
        sa.Column("commodity_name", sa.String(100)),
        sa.Column("region_name", sa.String(100)),
        sa.Column("entity_id", sa.String(50)),
        sa.Column("entity_name", sa.String(100)),
        sa.Column("frequency", sa.String(20)),
        sa.Column("price", sa.Numeric(14, 4)),
        sa.Column("unit", sa.String(20)),
        sa.Column("valid_price_flag", sa.Integer()),
        sa.Column("is_imputed", sa.Boolean()),
        sa.Column("missing_gap_length", sa.Integer()),
        sa.Column("anomaly_candidate", sa.Boolean()),
        sa.Column("data_quality_score", sa.Numeric(8, 4)),
        sa.Column("missing_rate", sa.Numeric(8, 6)),
        sa.Column("status", sa.String(30)),
        sa.Column("source_count", sa.Numeric(8, 2)),
        sa.Column("day_of_week", sa.Integer()),
        sa.Column("week_of_year", sa.Integer()),
        sa.Column("month", sa.Integer()),
        sa.Column("quarter", sa.Integer()),
        sa.Column("is_weekend", sa.Integer()),
        sa.Column("is_month_start", sa.Integer()),
        sa.Column("is_month_end", sa.Integer()),
        sa.Column("price_lag_1", sa.Numeric(14, 4)),
        sa.Column("price_lag_3", sa.Numeric(14, 4)),
        sa.Column("price_lag_7", sa.Numeric(14, 4)),
        sa.Column("price_lag_14", sa.Numeric(14, 4)),
        sa.Column("price_lag_30", sa.Numeric(14, 4)),
        sa.Column("rolling_mean_7", sa.Numeric(14, 4)),
        sa.Column("rolling_mean_14", sa.Numeric(14, 4)),
        sa.Column("rolling_mean_30", sa.Numeric(14, 4)),
        sa.Column("rolling_std_7", sa.Numeric(14, 4)),
        sa.Column("rolling_min_7", sa.Numeric(14, 4)),
        sa.Column("rolling_max_7", sa.Numeric(14, 4)),
        sa.Column("rolling_median_7", sa.Numeric(14, 4)),
        sa.Column("rolling_median_30", sa.Numeric(14, 4)),
        sa.Column("price_change_1d", sa.Numeric(14, 4)),
        sa.Column("price_change_7d", sa.Numeric(14, 4)),
        sa.Column("price_change_30d", sa.Numeric(14, 4)),
        sa.Column("pct_change_1d", sa.Numeric(12, 6)),
        sa.Column("pct_change_7d", sa.Numeric(12, 6)),
        sa.Column("pct_change_30d", sa.Numeric(12, 6)),
        sa.Column("missing_rate_30d", sa.Numeric(8, 6)),
        sa.Column("is_imputed_count_30d", sa.Integer()),
        sa.Column("ramadan_flag", sa.Integer()),
        sa.Column("lebaran_minus_21", sa.Integer()),
        sa.Column("lebaran_minus_14", sa.Integer()),
        sa.Column("lebaran_minus_7", sa.Integer()),
        sa.Column("lebaran_plus_7", sa.Integer()),
        sa.Column("nataru_minus_14", sa.Integer()),
        sa.Column("idul_adha_window", sa.Integer()),
        sa.Column("school_holiday_flag", sa.Integer()),
        sa.Column("harvest_flag", sa.Integer()),
        sa.Column("rainfall_1d", sa.Numeric(10, 4)),
        sa.Column("temperature_avg", sa.Numeric(6, 2)),
        sa.Column("weather_station_count", sa.Integer()),
        sa.Column("rainfall_anomaly", sa.Numeric(10, 4)),
        sa.Column("extreme_weather_flag", sa.Integer()),
        sa.Column("inflation_mom_lag_1", sa.Numeric(10, 6)),
        sa.Column("inflation_yoy_lag_1", sa.Numeric(10, 6)),
        sa.Column("usd_idr_change", sa.Numeric(12, 8)),
        sa.Column("bi_rate", sa.Numeric(8, 4)),
        sa.Column("fuel_price_flag", sa.Integer()),
        sa.Column("target_h7", sa.Numeric(14, 4)),
        sa.Column("target_h14", sa.Numeric(14, 4)),
        sa.Column("target_h30", sa.Numeric(14, 4)),
        sa.Column("has_weather", sa.Integer()),
        sa.Column("has_macro", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint(
            "date", "commodity_id", "region_id", "entity_level", "series_family",
            name="pk_feature_store_daily",
        ),
    )
    op.create_index(
        "idx_fs_date_commodity_region", "feature_store_daily",
        ["date", "commodity_id", "region_id"],
    )
    op.create_index("idx_fs_split", "feature_store_daily", ["split"])
    op.create_index("idx_fs_row_role", "feature_store_daily", ["row_role"])


def downgrade() -> None:
    op.drop_index("idx_fs_row_role", table_name="feature_store_daily")
    op.drop_index("idx_fs_split", table_name="feature_store_daily")
    op.drop_index("idx_fs_date_commodity_region", table_name="feature_store_daily")
    op.drop_table("feature_store_daily")
