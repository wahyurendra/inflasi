from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.insight_generator import InsightGenerator

router = APIRouter()


@router.get("/latest")
async def get_latest_insight(
    tipe: str = Query("harian", description="harian|mingguan"),
    db: AsyncSession = Depends(get_db),
):
    """Get insight terbaru."""
    generator = InsightGenerator(db)
    return await generator.get_latest(tipe)


@router.post("/generate")
async def generate_insight(
    tipe: str = Query("harian"),
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate insight baru."""
    generator = InsightGenerator(db)
    result = await generator.generate(tipe, tanggal or date.today())
    return {"status": "ok", "insight": result}
