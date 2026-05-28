from fastapi import APIRouter
from pydantic import BaseModel

from app.models.surplus_deficit import SurplusDeficitClassifier

router = APIRouter()
_clf = SurplusDeficitClassifier()


class SDRequest(BaseModel):
    stock: float
    demand: float


@router.post("/classify")
async def classify(body: SDRequest) -> dict:
    return _clf.classify(body.stock, body.demand)
