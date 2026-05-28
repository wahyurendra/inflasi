from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import FactPriceDaily, DimCommodity, DimRegion

router = APIRouter()


def _price_to_dict(p: FactPriceDaily) -> dict:
    return {
        "tanggal": p.tanggal.isoformat(),
        "harga": float(p.harga),
        "perubahanHarian": float(p.perubahan_harian) if p.perubahan_harian else None,
        "perubahanMingguan": float(p.perubahan_mingguan) if p.perubahan_mingguan else None,
        "perubahanBulanan": float(p.perubahan_bulanan) if p.perubahan_bulanan else None,
        "commodity": {
            "kode": p.commodity.kode_komoditas,
            "nama": p.commodity.nama_display,
        },
        "region": {
            "kode": p.region.kode_wilayah,
            "nama": p.region.nama_provinsi,
        },
    }


@router.get("/list")
async def list_prices(
    commodity: str = Query(None),
    region: str = Query("00"),
    days: int = Query(30),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days)
    q = select(FactPriceDaily).where(FactPriceDaily.tanggal >= since)

    if commodity:
        sub = select(DimCommodity.id).where(DimCommodity.kode_komoditas == commodity)
        q = q.where(FactPriceDaily.commodity_id.in_(sub))
    if region:
        sub_r = select(DimRegion.id).where(DimRegion.kode_wilayah == region)
        q = q.where(FactPriceDaily.region_id.in_(sub_r))

    q = q.order_by(FactPriceDaily.tanggal.desc()).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return {"data": [_price_to_dict(p) for p in rows], "count": len(rows)}


@router.get("/daily")
async def daily_prices(
    commodity: str = Query(None),
    region: str = Query("00"),
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days)
    q = select(FactPriceDaily).where(FactPriceDaily.tanggal >= since)

    if commodity:
        sub = select(DimCommodity.id).where(DimCommodity.kode_komoditas == commodity)
        q = q.where(FactPriceDaily.commodity_id.in_(sub))
    if region:
        sub_r = select(DimRegion.id).where(DimRegion.kode_wilayah == region)
        q = q.where(FactPriceDaily.region_id.in_(sub_r))

    q = q.order_by(FactPriceDaily.tanggal.desc())
    result = await db.execute(q)
    rows = result.scalars().all()
    return {"data": [_price_to_dict(p) for p in rows], "count": len(rows)}


@router.get("/trends")
async def price_trends(
    commodity: str = Query(...),
    region: str = Query("00"),
    days: int = Query(90),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days)
    sub_c = select(DimCommodity.id).where(DimCommodity.kode_komoditas == commodity)
    sub_r = select(DimRegion.id).where(DimRegion.kode_wilayah == region)

    q = (
        select(FactPriceDaily)
        .where(
            FactPriceDaily.commodity_id.in_(sub_c),
            FactPriceDaily.region_id.in_(sub_r),
            FactPriceDaily.tanggal >= since,
        )
        .order_by(FactPriceDaily.tanggal.asc())
    )
    result = await db.execute(q)
    rows = result.scalars().all()
    return {"data": [_price_to_dict(p) for p in rows]}
