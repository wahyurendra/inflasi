"""Pydantic schema for feature rows passed to the multivariate forecaster.

Mirrors the columns of `unified_ready_dataset` / `feature_store_daily`. All
engineered features are optional — only `date` and `price` are required.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class FeatureRow(BaseModel):
    date: date
    price: float | None = None

    # Identity (optional context)
    commodity_id: str | None = None
    region_id: str | None = None
    entity_level: str | None = None
    series_family: str | None = None

    # Calendar
    day_of_week: int | None = None
    week_of_year: int | None = None
    month: int | None = None
    quarter: int | None = None
    is_weekend: int | None = None
    is_month_start: int | None = None
    is_month_end: int | None = None

    # Holiday flags
    ramadan_flag: int | None = None
    lebaran_minus_21: int | None = None
    lebaran_minus_14: int | None = None
    lebaran_minus_7: int | None = None
    lebaran_plus_7: int | None = None
    nataru_minus_14: int | None = None
    idul_adha_window: int | None = None
    school_holiday_flag: int | None = None
    harvest_flag: int | None = None

    # Lags
    price_lag_1: float | None = None
    price_lag_3: float | None = None
    price_lag_7: float | None = None
    price_lag_14: float | None = None
    price_lag_30: float | None = None

    # Rolling
    rolling_mean_7: float | None = None
    rolling_mean_14: float | None = None
    rolling_mean_30: float | None = None
    rolling_std_7: float | None = None
    rolling_min_7: float | None = None
    rolling_max_7: float | None = None
    rolling_median_7: float | None = None
    rolling_median_30: float | None = None

    # Weather
    rainfall_1d: float | None = None
    temperature_avg: float | None = None
    weather_station_count: int | None = None
    rainfall_anomaly: float | None = None
    extreme_weather_flag: int | None = None

    # Macro
    inflation_mom_lag_1: float | None = None
    inflation_yoy_lag_1: float | None = None
    usd_idr_change: float | None = None
    bi_rate: float | None = None
    fuel_price_flag: int | None = None

    # Quality
    valid_price_flag: int | None = None
    is_imputed: bool | None = None
    data_quality_score: float | None = None

    model_config = {"extra": "ignore"}


class PredictFeaturesRequest(BaseModel):
    features: list[FeatureRow] = Field(..., min_length=1)
    horizons: list[int] = Field(default_factory=lambda: [7, 14, 30])
    model: str = Field("ensemble", description="ensemble | prophet | arima | tft")


class PredictFeaturesResponse(BaseModel):
    horizons: dict[str, list[float]]
    model: str
    models_used: dict[str, bool]
