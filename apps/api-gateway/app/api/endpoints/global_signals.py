from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import (
    ExtFaoFoodPrice, ExtCommodityPrice, ExtExchangeRate,
    ExtEnergyPrice, ExtSupplyChainIndex, ExtNewsSignal,
)

router = APIRouter()


@router.get("/")
async def global_signals(
    limit: int = Query(12),
    db: AsyncSession = Depends(get_db),
):
    # FAO Food Price Index
    fao_q = await db.execute(
        select(ExtFaoFoodPrice).order_by(ExtFaoFoodPrice.periode.desc()).limit(limit)
    )
    fao = [
        {
            "periode": r.periode.isoformat(),
            "overall": float(r.index_overall) if r.index_overall else None,
            "cereals": float(r.index_cereals) if r.index_cereals else None,
            "vegOil": float(r.index_veg_oil) if r.index_veg_oil else None,
            "dairy": float(r.index_dairy) if r.index_dairy else None,
            "meat": float(r.index_meat) if r.index_meat else None,
            "sugar": float(r.index_sugar) if r.index_sugar else None,
        }
        for r in fao_q.scalars().all()
    ]

    # Commodity prices — group by commodity, latest per commodity
    comm_q = await db.execute(
        select(ExtCommodityPrice).order_by(ExtCommodityPrice.periode.desc()).limit(50)
    )
    commodities_map: dict = {}
    for r in comm_q.scalars().all():
        if r.commodity not in commodities_map:
            commodities_map[r.commodity] = {
                "price": float(r.price),
                "changePct": float(r.change_pct) if r.change_pct else None,
                "unit": r.unit,
                "periode": r.periode.isoformat(),
            }

    # Exchange rate
    kurs_q = await db.execute(
        select(ExtExchangeRate).order_by(ExtExchangeRate.tanggal.desc()).limit(limit)
    )
    kurs = [
        {
            "tanggal": r.tanggal.isoformat(),
            "kursTengah": float(r.kurs_tengah) if r.kurs_tengah else None,
            "changePct": float(r.change_pct) if r.change_pct else None,
        }
        for r in kurs_q.scalars().all()
    ]

    # Energy prices
    energy_q = await db.execute(
        select(ExtEnergyPrice).order_by(ExtEnergyPrice.tanggal.desc()).limit(limit * 3)
    )
    energy = [
        {
            "tanggal": r.tanggal.isoformat(),
            "commodity": r.commodity,
            "price": float(r.price),
            "changePct": float(r.change_pct) if r.change_pct else None,
        }
        for r in energy_q.scalars().all()
    ]

    # Supply chain index
    sc_q = await db.execute(
        select(ExtSupplyChainIndex).order_by(ExtSupplyChainIndex.periode.desc()).limit(limit)
    )
    supply_chain = [
        {"periode": r.periode.isoformat(), "gscpi": float(r.gscpi)}
        for r in sc_q.scalars().all()
    ]

    # News signals
    news_q = await db.execute(
        select(ExtNewsSignal).order_by(ExtNewsSignal.tanggal.desc()).limit(20)
    )
    news = [
        {
            "tanggal": r.tanggal.isoformat(),
            "kategori": r.kategori,
            "judul": r.judul,
            "sumber": r.sumber,
            "url": r.url,
            "sentimen": r.sentimen,
            "relevansi": float(r.relevansi) if r.relevansi else None,
        }
        for r in news_q.scalars().all()
    ]

    return {
        "fao": fao,
        "commodities": commodities_map,
        "kurs": kurs,
        "energy": energy,
        "supplyChain": supply_chain,
        "news": news,
    }
