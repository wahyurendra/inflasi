from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import (
    DimRegion, FactPriceDaily, AnalyticsAlert, AnalyticsRiskScore, DimCommodity,
)
from datetime import date, timedelta

router = APIRouter()


@router.get("/")
async def list_regions(
    level: str = Query(None),
    active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    q = select(DimRegion).where(DimRegion.is_active == active)
    if level:
        q = q.where(DimRegion.level_wilayah == level)
    q = q.order_by(DimRegion.nama_provinsi)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "kodeWilayah": r.kode_wilayah,
            "namaProvinsi": r.nama_provinsi,
            "namaKabKota": r.nama_kab_kota,
            "levelWilayah": r.level_wilayah,
            "latitude": float(r.latitude) if r.latitude else None,
            "longitude": float(r.longitude) if r.longitude else None,
        }
        for r in rows
    ]


@router.get("/heatmap")
async def region_heatmap(db: AsyncSession = Depends(get_db)):
    d7 = date.today() - timedelta(days=7)
    regions = await db.execute(
        select(DimRegion).where(DimRegion.level_wilayah == "provinsi", DimRegion.is_active == True)
    )

    data = []
    for r in regions.scalars().all():
        # Avg price change last 7d
        avg_q = await db.execute(
            select(func.avg(FactPriceDaily.perubahan_harian))
            .where(FactPriceDaily.region_id == r.id, FactPriceDaily.tanggal >= d7)
        )
        avg_change = avg_q.scalar() or 0

        # Alert count
        alert_q = await db.execute(
            select(func.count(AnalyticsAlert.id))
            .where(AnalyticsAlert.region_id == r.id, AnalyticsAlert.is_active == True)
        )
        alert_count = alert_q.scalar() or 0

        # Latest risk category
        risk_q = await db.execute(
            select(AnalyticsRiskScore.risk_category)
            .where(AnalyticsRiskScore.region_id == r.id)
            .order_by(AnalyticsRiskScore.tanggal.desc())
            .limit(1)
        )
        risk_cat = risk_q.scalar() or "rendah"

        data.append({
            "kodeWilayah": r.kode_wilayah,
            "namaProvinsi": r.nama_provinsi,
            "avgPriceChange": round(float(avg_change), 2),
            "alertCount": alert_count,
            "riskCategory": risk_cat,
        })

    return {"data": data}
