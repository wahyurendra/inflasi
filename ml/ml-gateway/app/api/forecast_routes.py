from fastapi import APIRouter
from pydantic import BaseModel

from app.models.forecaster import EnsembleForecaster

router = APIRouter()
_forecaster = EnsembleForecaster()


class ForecastRequest(BaseModel):
    series: list[float]          # historical daily prices, oldest -> newest
    horizon_days: int = 30


@router.post("/prices")
async def forecast_prices(body: ForecastRequest) -> dict:
    return _forecaster.predict(body.series, body.horizon_days)
