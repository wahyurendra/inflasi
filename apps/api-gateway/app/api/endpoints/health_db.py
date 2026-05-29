"""Health endpoint — enriched with forecast/model freshness so an operator can
see at a glance whether the prediction pipeline is keeping up."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import (
    AnalyticsAlert,
    AnalyticsForecast,
    DimRegion,
    FactPriceDaily,
    ModelRegistry,
    ModelTrainingRun,
)

router = APIRouter()


@router.get("/db-stats")
async def db_stats(db: AsyncSession = Depends(get_db)):
    region_count = (await db.execute(select(func.count(DimRegion.id)))).scalar() or 0
    latest_price = (await db.execute(
        select(FactPriceDaily.tanggal).order_by(FactPriceDaily.tanggal.desc()).limit(1)
    )).scalar()
    active_alerts = (await db.execute(
        select(func.count(AnalyticsAlert.id)).where(AnalyticsAlert.is_active.is_(True))
    )).scalar() or 0

    active_models = (await db.execute(
        select(func.count(ModelRegistry.id)).where(ModelRegistry.is_active.is_(True))
    )).scalar() or 0
    latest_forecast = (await db.execute(
        select(AnalyticsForecast.created_at)
        .order_by(AnalyticsForecast.created_at.desc())
        .limit(1)
    )).scalar()
    latest_training = (await db.execute(
        select(ModelTrainingRun.started_at)
        .order_by(ModelTrainingRun.started_at.desc())
        .limit(1)
    )).scalar()

    feature_coverage = (await db.execute(
        text("SELECT MAX(date) AS last_date FROM feature_store_daily")
    )).first()
    monthly_feature_coverage = (await db.execute(
        text("SELECT MAX(period) AS last_period FROM feature_store_monthly")
    )).first()

    return {
        "connected": True,
        "regions": region_count,
        "latestPriceDate": latest_price.isoformat() if latest_price else None,
        "activeAlerts": active_alerts,
        "models": {
            "active": active_models,
            "latestForecastAt": latest_forecast.isoformat() if latest_forecast else None,
            "latestTrainingAt": latest_training.isoformat() if latest_training else None,
        },
        "featureStore": {
            "dailyLastDate": (
                feature_coverage.last_date.isoformat()
                if feature_coverage and feature_coverage.last_date else None
            ),
            "monthlyLastPeriod": (
                monthly_feature_coverage.last_period.isoformat()
                if monthly_feature_coverage and monthly_feature_coverage.last_period else None
            ),
        },
    }
