from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.supply_demand import SupplyDemandService

router = APIRouter()


@router.get("/")
async def get_recommendations(
    tanggal: date | None = Query(None, description="Tanggal acuan (default: hari ini)"),
    db: AsyncSession = Depends(get_db),
):
    """Get redistribution recommendations based on supply-demand analysis."""
    service = SupplyDemandService(db)
    data = await service.get_recommendations(tanggal)
    return {"data": data}
