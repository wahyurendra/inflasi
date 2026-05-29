"""Pydantic schemas for the v2 forecast API.

`PriceForecastRequest` matches the spec's POST /api/v1/forecast/price body.
`PriceForecastResponse` carries point + p10/p50/p90 + risk + drivers + components.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class PriceForecastRequest(BaseModel):
    commodity_id: int = Field(..., description="dim_commodity.id")
    region_id: int = Field(..., description="dim_region.id")
    horizon: int = Field(7, ge=1, le=60, description="Horizon hari ke depan")


class DriverImpact(BaseModel):
    feature: str
    impact: float


class ComponentPrediction(BaseModel):
    model_name: str
    model_type: str
    model_version: str | None = None
    prediction: float | None = None
    p10: float | None = None
    p50: float | None = None
    p90: float | None = None
    model_weight: float | None = None
    model_confidence: float | None = None


class ForecastPointSchema(BaseModel):
    target_date: date
    yhat: float
    yhat_lower: float
    yhat_upper: float
    p10: float
    p50: float
    p90: float
    risk_level: str
    confidence_score: float
    top_drivers: list[DriverImpact] = []
    model_contribution: dict[str, float] = {}
    components: list[ComponentPrediction] = []


class PriceForecastResponse(BaseModel):
    commodity_id: int
    region_id: int
    horizon: int
    model_version: str
    points: list[ForecastPointSchema]


# ── Admin: model registry ────────────────────────────────────

class ModelRegistryRow(BaseModel):
    id: int
    model_name: str
    model_type: str
    target_type: str
    horizon: int | None = None
    version: str
    artifact_path: str
    feature_set_version: str | None = None
    is_active: bool
    metrics: dict[str, Any] | None = None
    params: dict[str, Any] | None = None


class ModelRegisterRequest(BaseModel):
    model_name: str
    model_type: str
    target_type: str
    version: str
    artifact_path: str
    horizon: int | None = None
    feature_set_version: str | None = None
    training_start_date: date | None = None
    training_end_date: date | None = None
    metrics: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    is_active: bool = False
