from fastapi import APIRouter
from pydantic import BaseModel

from app.models.anomaly import AnomalyDetector

router = APIRouter()
_detector = AnomalyDetector()


class AnomalyRequest(BaseModel):
    history: list[float]
    value: float
    z_threshold: float = 3.0


@router.post("/detect")
async def detect(body: AnomalyRequest) -> dict:
    return _detector.detect(body.history, body.value, body.z_threshold)
