from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import (
    FactPriceDaily, AnalyticsAlert, AnalyticsInsight,
    AnalyticsForecast, AnalyticsRiskScore, ExtExchangeRate,
    DimCommodity,
)

router = APIRouter()


@router.get("/context/dashboard")
async def dashboard_context(db: AsyncSession = Depends(get_db)):
    """Gather all dashboard data for AI chat context."""
    # Latest data date
    latest_q = await db.execute(
        select(FactPriceDaily.tanggal).order_by(FactPriceDaily.tanggal.desc()).limit(1)
    )
    latest_date = latest_q.scalar()
    tanggal_data = latest_date.isoformat() if latest_date else None

    # Recent prices (last 7 days, national)
    d7 = date.today() - timedelta(days=7)
    prices_q = await db.execute(
        select(FactPriceDaily)
        .where(FactPriceDaily.tanggal >= d7)
        .order_by(FactPriceDaily.tanggal.desc())
        .limit(50)
    )
    prices = [
        {
            "tanggal": p.tanggal.isoformat(),
            "komoditas": p.commodity.nama_display if p.commodity else None,
            "harga": float(p.harga),
            "perubahan": float(p.perubahan_harian) if p.perubahan_harian else None,
        }
        for p in prices_q.scalars().all()
    ]

    # Active alerts
    alerts_q = await db.execute(
        select(AnalyticsAlert)
        .where(AnalyticsAlert.is_active == True)
        .order_by(AnalyticsAlert.tanggal.desc())
        .limit(10)
    )
    alerts = [
        {
            "judul": a.judul,
            "deskripsi": a.deskripsi,
            "severity": a.severity,
            "komoditas": a.commodity.nama_display if a.commodity else None,
            "wilayah": a.region.nama_provinsi if a.region else None,
        }
        for a in alerts_q.scalars().all()
    ]

    # Latest insight
    insight_q = await db.execute(
        select(AnalyticsInsight).order_by(AnalyticsInsight.tanggal.desc()).limit(1)
    )
    insight = insight_q.scalar()

    # Forecasts
    forecast_q = await db.execute(
        select(AnalyticsForecast)
        .order_by(AnalyticsForecast.tanggal.desc())
        .limit(20)
    )
    forecasts = [
        {
            "komoditas": f.commodity.nama_display if f.commodity else None,
            "tanggal": f.tanggal.isoformat(),
            "prediksi": float(f.yhat),
            "bawah": float(f.yhat_lower),
            "atas": float(f.yhat_upper),
        }
        for f in forecast_q.scalars().all()
    ]

    # Risk scores
    risk_q = await db.execute(
        select(AnalyticsRiskScore)
        .order_by(AnalyticsRiskScore.risk_score_total.desc())
        .limit(10)
    )
    risks = [
        {
            "komoditas": r.commodity.nama_display if r.commodity else None,
            "wilayah": r.region.nama_provinsi if r.region else None,
            "skor": float(r.risk_score_total) if r.risk_score_total else 0,
            "kategori": r.risk_category,
        }
        for r in risk_q.scalars().all()
    ]

    # Exchange rate
    kurs_q = await db.execute(
        select(ExtExchangeRate).order_by(ExtExchangeRate.tanggal.desc()).limit(1)
    )
    kurs = kurs_q.scalar()

    return {
        "tanggalData": tanggal_data,
        "harga": prices,
        "alerts": alerts,
        "insight": {
            "judul": insight.judul if insight else None,
            "konten": insight.konten if insight else None,
        },
        "forecast": forecasts,
        "riskScores": risks,
        "kurs": {
            "kursTengah": float(kurs.kurs_tengah) if kurs and kurs.kurs_tengah else None,
            "changePct": float(kurs.change_pct) if kurs and kurs.change_pct else None,
        },
    }


class SearchRequest(BaseModel):
    query: str


@router.post("/context/search")
async def search_context(body: SearchRequest, db: AsyncSession = Depends(get_db)):
    """Search for commodity data based on query."""
    query = body.query.lower()

    # Try to find matching commodity
    commodities = await db.execute(select(DimCommodity))
    matched = None
    for c in commodities.scalars().all():
        if (query in c.nama_display.lower() or query in c.nama_komoditas.lower()
                or query in c.kode_komoditas.lower()):
            matched = c
            break

    context: dict = {}
    if matched:
        # Price data
        d30 = date.today() - timedelta(days=30)
        prices_q = await db.execute(
            select(FactPriceDaily)
            .where(FactPriceDaily.commodity_id == matched.id, FactPriceDaily.tanggal >= d30)
            .order_by(FactPriceDaily.tanggal.desc())
            .limit(30)
        )
        context["hargaKomoditas"] = [
            {
                "tanggal": p.tanggal.isoformat(),
                "wilayah": p.region.nama_provinsi if p.region else None,
                "harga": float(p.harga),
                "perubahanHarian": float(p.perubahan_harian) if p.perubahan_harian else None,
                "perubahanMingguan": float(p.perubahan_mingguan) if p.perubahan_mingguan else None,
            }
            for p in prices_q.scalars().all()
        ]

        # Forecasts
        forecast_q = await db.execute(
            select(AnalyticsForecast)
            .where(AnalyticsForecast.commodity_id == matched.id)
            .order_by(AnalyticsForecast.tanggal.desc())
            .limit(14)
        )
        context["forecast"] = [
            {"tanggal": f.tanggal.isoformat(), "prediksi": float(f.yhat)}
            for f in forecast_q.scalars().all()
        ]

        # Alerts
        alerts_q = await db.execute(
            select(AnalyticsAlert)
            .where(AnalyticsAlert.commodity_id == matched.id, AnalyticsAlert.is_active == True)
            .limit(5)
        )
        context["alertAktif"] = [
            {
                "judul": a.judul,
                "deskripsi": a.deskripsi,
                "severity": a.severity,
                "komoditas": a.commodity.nama_display if a.commodity else None,
                "wilayah": a.region.nama_provinsi if a.region else None,
            }
            for a in alerts_q.scalars().all()
        ]

    return {"context": context, "query": body.query}
