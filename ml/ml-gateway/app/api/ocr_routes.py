from fastapi import APIRouter
from pydantic import BaseModel

from app.models.ocr import OCREngine

router = APIRouter()
_ocr = OCREngine()


class OCRRequest(BaseModel):
    image_url: str
    reported_price: float
    tolerance: float = 0.1


@router.post("/verify")
async def verify(body: OCRRequest) -> dict:
    return await _ocr.verify(body.image_url, body.reported_price, body.tolerance)
