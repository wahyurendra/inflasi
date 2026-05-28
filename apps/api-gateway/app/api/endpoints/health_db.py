from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import DimRegion, FactPriceDaily, AnalyticsAlert

router = APIRouter()


@router.get("/db-stats")
async def db_stats(db: AsyncSession = Depends(get_db)):
    region_count = await db.execute(select(func.count(DimRegion.id)))
    latest_price = await db.execute(
        select(FactPriceDaily.tanggal).order_by(FactPriceDaily.tanggal.desc()).limit(1)
    )
    active_alerts = await db.execute(
        select(func.count(AnalyticsAlert.id)).where(AnalyticsAlert.is_active == True)
    )

    return {
        "connected": True,
        "regions": region_count.scalar() or 0,
        "latestPriceDate": lp.isoformat() if (lp := latest_price.scalar()) else None,
        "activeAlerts": active_alerts.scalar() or 0,
    }
