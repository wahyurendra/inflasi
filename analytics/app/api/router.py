from fastapi import APIRouter

from app.api.endpoints import analytics, alerts, insights

router = APIRouter()

router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
router.include_router(insights.router, prefix="/insights", tags=["insights"])
