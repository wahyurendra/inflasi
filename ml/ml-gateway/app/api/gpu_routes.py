"""Internal GPU-only operations called by the always-on CPU gateway."""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.loaders.tft_loader import TFTLoader

router = APIRouter()
_tft = TFTLoader(allow_remote=False)


class TFTPredictRequest(BaseModel):
    features: list[dict[str, Any]] = Field(..., min_length=1)
    horizon: int = Field(..., ge=1, le=60)


@router.post("/tft/predict")
def predict_tft(body: TFTPredictRequest) -> dict[str, Any]:
    """Run only TFT inference; ensemble orchestration stays on the CPU gateway."""
    result = _tft.predict(pd.DataFrame(body.features), body.horizon)
    if result is None:
        raise HTTPException(status_code=503, detail="TFT GPU inference unavailable")
    return result
