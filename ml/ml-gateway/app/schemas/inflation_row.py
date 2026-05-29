"""Pydantic schemas for the monthly inflation forecast route.

The api-gateway sends a window of recent `feature_store_monthly` rows; the
ml-gateway returns p10/p50/p90 for M+1, M+3, M+6 plus per-base-model
contributions when the registry has trained inflation models available.

Targets stay optional — at inference time the most-recent rows are unlabeled
(future months haven't happened yet), but during evaluation the api-gateway
may pass labeled rows to backtest.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class InflationFeatureRow(BaseModel):
    period: date
    region_id: int | str | None = None
    target_type: str = "inflation"
    level_wilayah: str | None = None

    # CPI core
    ihk: float | None = None
    inflasi_mtm: float | None = None
    inflasi_yoy: float | None = None
    inflasi_ytd: float | None = None

    # Lags
    inflasi_lag_1: float | None = None
    inflasi_lag_3: float | None = None
    inflasi_lag_6: float | None = None
    inflasi_lag_12: float | None = None

    # Rolling
    inflasi_rolling_3: float | None = None
    inflasi_rolling_6: float | None = None
    inflasi_std_3: float | None = None
    inflasi_std_6: float | None = None

    # Food
    food_price_index: float | None = None
    food_price_change_mom: float | None = None
    food_price_anomaly: float | None = None
    beras_change_mom: float | None = None
    cabai_merah_change_mom: float | None = None
    bawang_merah_change_mom: float | None = None
    telur_change_mom: float | None = None
    ayam_change_mom: float | None = None
    minyak_goreng_change_mom: float | None = None

    # Weather + macro
    rainfall_mean: float | None = None
    rainfall_anomaly: float | None = None
    temperature_mean: float | None = None
    extreme_weather_days: int | None = None
    kurs_usd_idr: float | None = None
    kurs_change_mom: float | None = None
    bbm_price: float | None = None
    bbm_change_mom: float | None = None

    # Calendar
    month: int | None = None
    quarter: int | None = None
    ramadan_flag: int | None = None
    lebaran_flag: int | None = None
    idul_adha_flag: int | None = None
    nataru_flag: int | None = None
    harvest_flag: int | None = None

    # Targets (optional — only present when labeled)
    target_inflation_m1: float | None = None
    target_inflation_m3: float | None = None
    target_inflation_m6: float | None = None

    model_config = {"extra": "ignore"}


class PredictInflationRequest(BaseModel):
    features: list[InflationFeatureRow] = Field(..., min_length=1)
    horizons: list[int] = Field(default_factory=lambda: [1, 3, 6])
    model: str = Field("ensemble", description="ensemble | lightgbm | sarimax")
