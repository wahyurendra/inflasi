"""ML gateway inflation route — monthly inflation forecasts.

`POST /inflation/predict` consumes `feature_store_monthly` rows and returns
the same shape as `/forecast/predict`: point + p10/p50/p90 + per-base-model
components. The api-gateway's prediction service treats both routes
uniformly, so the schema is intentionally aligned.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.inflation_forecaster import InflationForecaster
from app.schemas.inflation_row import PredictInflationRequest

router = APIRouter()
_forecaster = InflationForecaster()


@router.post("/predict")
async def predict_inflation(body: PredictInflationRequest) -> dict:
    rows = [row.model_dump(mode="json") for row in body.features]
    horizons = sorted(set(body.horizons))
    return _forecaster.predict_features(rows, horizons, body.model)
