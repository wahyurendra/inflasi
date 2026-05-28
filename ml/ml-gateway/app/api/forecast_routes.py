from fastapi import APIRouter
from pydantic import BaseModel

from app.models.forecaster import EnsembleForecaster
from app.schemas.feature_row import PredictFeaturesRequest

router = APIRouter()
_forecaster = EnsembleForecaster()


class ForecastRequest(BaseModel):
    series: list[float]          # historical daily prices, oldest -> newest
    horizon_days: int = 30


@router.post("/prices")
async def forecast_prices(body: ForecastRequest) -> dict:
    """Legacy univariate forecast — price series only."""
    return _forecaster.predict(body.series, body.horizon_days)


@router.post("/predict")
async def forecast_predict(body: PredictFeaturesRequest) -> dict:
    """Multivariate forecast — consumes feature_store_daily rows.

    Returns predictions per requested horizon (e.g. {"7": [...], "14": [...], "30": [...]}).
    """
    rows = [row.model_dump(mode="json") for row in body.features]
    horizons = sorted(set(body.horizons))
    return _forecaster.predict_features(rows, horizons, body.model)
