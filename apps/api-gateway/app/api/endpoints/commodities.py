from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import DimCommodity, FactPriceDaily

router = APIRouter()


@router.get("/")
async def list_commodities(
    mvp: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    q = select(DimCommodity)
    if mvp:
        q = q.where(DimCommodity.is_mvp == True)
    q = q.order_by(DimCommodity.nama_display)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": c.id,
            "kodeKomoditas": c.kode_komoditas,
            "namaKomoditas": c.nama_komoditas,
            "namaDisplay": c.nama_display,
            "kategori": c.kategori,
            "satuan": c.satuan,
            "isStrategis": c.is_strategis,
        }
        for c in rows
    ]


@router.get("/ranking")
async def commodity_ranking(
    sort: str = Query("weekly_change"),
    limit: int = Query(8),
    db: AsyncSession = Depends(get_db),
):
    commodities = await db.execute(
        select(DimCommodity).where(DimCommodity.is_mvp == True)
    )
    data = []
    for c in commodities.scalars().all():
        price_q = await db.execute(
            select(FactPriceDaily)
            .where(FactPriceDaily.commodity_id == c.id)
            .order_by(FactPriceDaily.tanggal.desc())
            .limit(1)
        )
        p = price_q.scalar()
        data.append({
            "kodeKomoditas": c.kode_komoditas,
            "namaDisplay": c.nama_display,
            "kategori": c.kategori,
            "satuan": c.satuan,
            "hargaTerakhir": float(p.harga) if p else None,
            "perubahanHarian": float(p.perubahan_harian) if p and p.perubahan_harian else None,
            "perubahanMingguan": float(p.perubahan_mingguan) if p and p.perubahan_mingguan else None,
            "perubahanBulanan": float(p.perubahan_bulanan) if p and p.perubahan_bulanan else None,
        })

    sort_key = {
        "weekly_change": "perubahanMingguan",
        "daily_change": "perubahanHarian",
        "monthly_change": "perubahanBulanan",
    }.get(sort, "perubahanMingguan")

    data.sort(key=lambda x: abs(x.get(sort_key) or 0), reverse=True)
    return {"data": data[:limit]}
