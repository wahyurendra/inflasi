from fastapi import APIRouter
from pydantic import BaseModel

from app.models.trust import TrustScorer

router = APIRouter()
_scorer = TrustScorer()


class TrustRequest(BaseModel):
    approved: int = 0
    total: int = 0
    account_age_days: int = 0
    flagged: int = 0


@router.post("/score")
async def score(body: TrustRequest) -> dict:
    return _scorer.score(body.approved, body.total, body.account_age_days, body.flagged)
