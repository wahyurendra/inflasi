"""Feature store — wide table mirroring `unified_ready_dataset` CSV.

One row per (date, commodity, region, entity_level, series_family). All
engineered features (lags, rolling stats, calendar/holiday flags, weather,
macro, targets) materialized here for ML training & inference.
"""

from datetime import date as date_t, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Index, Integer, Numeric, PrimaryKeyConstraint,
    String, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FeatureStoreDaily(Base):
    __tablename__ = "feature_store_daily"

    date: Mapped[date_t] = mapped_column(Date)
    commodity_id: Mapped[str] = mapped_column(String(50))
    region_id: Mapped[str] = mapped_column(String(50))
    entity_level: Mapped[str] = mapped_column(String(20))
    series_family: Mapped[str] = mapped_column(String(50))

    split: Mapped[str | None] = mapped_column(String(20))
    row_role: Mapped[str | None] = mapped_column(String(50))
    commodity_name: Mapped[str | None] = mapped_column(String(100))
    region_name: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(50))
    entity_name: Mapped[str | None] = mapped_column(String(100))
    frequency: Mapped[str | None] = mapped_column(String(20))

    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    unit: Mapped[str | None] = mapped_column(String(20))
    valid_price_flag: Mapped[int | None] = mapped_column(Integer)
    is_imputed: Mapped[bool | None] = mapped_column(Boolean)
    missing_gap_length: Mapped[int | None] = mapped_column(Integer)
    anomaly_candidate: Mapped[bool | None] = mapped_column(Boolean)
    data_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    missing_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    status: Mapped[str | None] = mapped_column(String(30))
    source_count: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    day_of_week: Mapped[int | None] = mapped_column(Integer)
    week_of_year: Mapped[int | None] = mapped_column(Integer)
    month: Mapped[int | None] = mapped_column(Integer)
    quarter: Mapped[int | None] = mapped_column(Integer)
    is_weekend: Mapped[int | None] = mapped_column(Integer)
    is_month_start: Mapped[int | None] = mapped_column(Integer)
    is_month_end: Mapped[int | None] = mapped_column(Integer)

    price_lag_1: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    price_lag_3: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    price_lag_7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    price_lag_14: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    price_lag_30: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))

    rolling_mean_7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_mean_14: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_mean_30: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_std_7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_min_7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_max_7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_median_7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    rolling_median_30: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))

    price_change_1d: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    price_change_7d: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    price_change_30d: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    pct_change_1d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    pct_change_7d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    pct_change_30d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))

    missing_rate_30d: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    is_imputed_count_30d: Mapped[int | None] = mapped_column(Integer)

    ramadan_flag: Mapped[int | None] = mapped_column(Integer)
    lebaran_minus_21: Mapped[int | None] = mapped_column(Integer)
    lebaran_minus_14: Mapped[int | None] = mapped_column(Integer)
    lebaran_minus_7: Mapped[int | None] = mapped_column(Integer)
    lebaran_plus_7: Mapped[int | None] = mapped_column(Integer)
    nataru_minus_14: Mapped[int | None] = mapped_column(Integer)
    idul_adha_window: Mapped[int | None] = mapped_column(Integer)
    school_holiday_flag: Mapped[int | None] = mapped_column(Integer)
    harvest_flag: Mapped[int | None] = mapped_column(Integer)

    rainfall_1d: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    temperature_avg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    weather_station_count: Mapped[int | None] = mapped_column(Integer)
    rainfall_anomaly: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    extreme_weather_flag: Mapped[int | None] = mapped_column(Integer)

    inflation_mom_lag_1: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    inflation_yoy_lag_1: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    usd_idr_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    bi_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    fuel_price_flag: Mapped[int | None] = mapped_column(Integer)

    target_h7: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    target_h14: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    target_h30: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))

    has_weather: Mapped[int | None] = mapped_column(Integer)
    has_macro: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint(
            "date", "commodity_id", "region_id", "entity_level", "series_family",
            name="pk_feature_store_daily",
        ),
        Index("idx_fs_date_commodity_region", "date", "commodity_id", "region_id"),
        Index("idx_fs_split", "split"),
        Index("idx_fs_row_role", "row_role"),
    )
