from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import DimCommodity, DimRegion, FactPriceDaily, AnalyticsRiskScore

router = APIRouter()


@router.get("/volatility")
async def volatility_ranking(db: AsyncSession = Depends(get_db)):
    d30 = date.today() - timedelta(days=30)
    commodities = await db.execute(
        select(DimCommodity).where(DimCommodity.is_mvp == True)
    )
    data = []
    for c in commodities.scalars().all():
        prices_q = await db.execute(
            select(FactPriceDaily.harga)
            .where(FactPriceDaily.commodity_id == c.id, FactPriceDaily.tanggal >= d30)
        )
        prices = [float(p) for (p,) in prices_q.all()]
        if len(prices) < 5:
            continue

        import statistics
        mean = statistics.mean(prices)
        if mean == 0:
            continue
        stdev = statistics.stdev(prices)
        cv = (stdev / mean) * 100

        latest_q = await db.execute(
            select(FactPriceDaily.perubahan_mingguan)
            .where(FactPriceDaily.commodity_id == c.id)
            .order_by(FactPriceDaily.tanggal.desc())
            .limit(1)
        )
        weekly = latest_q.scalar()
        trend = "up" if (weekly and float(weekly) > 1) else "down" if (weekly and float(weekly) < -1) else "stable"

        data.append({
            "commodity": c.nama_display,
            "kode": c.kode_komoditas,
            "cv": round(cv, 2),
            "trend": trend,
        })

    data.sort(key=lambda x: x["cv"], reverse=True)
    return {"data": data}


@router.get("/price-gap")
async def price_gap(db: AsyncSession = Depends(get_db)):
    commodities = await db.execute(
        select(DimCommodity).where(DimCommodity.is_mvp == True)
    )
    data = []
    for c in commodities.scalars().all():
        prices_q = await db.execute(
            select(FactPriceDaily)
            .where(FactPriceDaily.commodity_id == c.id)
            .order_by(FactPriceDaily.tanggal.desc())
            .limit(100)
        )
        rows = prices_q.scalars().all()
        if not rows:
            continue

        # Group latest price by region
        region_prices: dict[int, float] = {}
        for p in rows:
            if p.region_id not in region_prices:
                region_prices[p.region_id] = float(p.harga)

        if len(region_prices) < 2:
            continue

        # Find highest and lowest
        max_rid = max(region_prices, key=lambda k: region_prices[k])
        min_rid = min(region_prices, key=lambda k: region_prices[k])
        highest = region_prices[max_rid]
        lowest = region_prices[min_rid]
        gap = highest - lowest
        gap_pct = (gap / lowest * 100) if lowest > 0 else 0

        # Get region names
        max_r = await db.execute(select(DimRegion.nama_provinsi).where(DimRegion.id == max_rid))
        min_r = await db.execute(select(DimRegion.nama_provinsi).where(DimRegion.id == min_rid))

        data.append({
            "commodity": c.nama_display,
            "highest": highest,
            "lowest": lowest,
            "gap": round(gap, 0),
            "gapPct": round(gap_pct, 1),
            "highRegion": max_r.scalar() or "",
            "lowRegion": min_r.scalar() or "",
        })

    data.sort(key=lambda x: x["gapPct"], reverse=True)
    return {"data": data}


@router.get("/comparison")
async def cross_region_comparison(
    commodity: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    provinces = await db.execute(
        select(DimRegion).where(DimRegion.level_wilayah == "provinsi", DimRegion.is_active == True)
    )
    prov_list = provinces.scalars().all()

    if commodity:
        # Single commodity across regions
        c_q = await db.execute(
            select(DimCommodity.id).where(DimCommodity.kode_komoditas == commodity)
        )
        cid = c_q.scalar()
        data = []
        for r in prov_list:
            price_q = await db.execute(
                select(FactPriceDaily.harga)
                .where(FactPriceDaily.commodity_id == cid, FactPriceDaily.region_id == r.id)
                .order_by(FactPriceDaily.tanggal.desc())
                .limit(1)
            )
            price = price_q.scalar()
            data.append({
                "region": r.nama_provinsi,
                "kode": r.kode_wilayah,
                "avgPrice": float(price) if price else None,
            })
        return {"data": data}

    # All MVP commodities across regions
    mvp_q = await db.execute(
        select(DimCommodity).where(DimCommodity.is_mvp == True)
    )
    mvp_commodities = mvp_q.scalars().all()

    data = []
    for r in prov_list:
        row: dict = {"region": r.nama_provinsi, "kode": r.kode_wilayah}
        for c in mvp_commodities:
            price_q = await db.execute(
                select(FactPriceDaily.harga)
                .where(FactPriceDaily.commodity_id == c.id, FactPriceDaily.region_id == r.id)
                .order_by(FactPriceDaily.tanggal.desc())
                .limit(1)
            )
            price = price_q.scalar()
            row[c.kode_komoditas] = float(price) if price else None
        data.append(row)

    return {"data": data}
