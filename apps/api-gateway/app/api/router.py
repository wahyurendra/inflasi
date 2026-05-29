from fastapi import APIRouter

from app.api.endpoints import (
    admin_models, internal_models,
    analytics, alerts, insights, forecast, drivers,
    regions, commodities, prices, inflation, global_signals,
    intelligence, gamification, health_db,
    auth_api, users, reports, notifications, ai_context,
    recommendations,
)

router = APIRouter()

# Existing
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
router.include_router(insights.router, prefix="/insights", tags=["insights"])
router.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])

# New — data
router.include_router(regions.router, prefix="/regions", tags=["regions"])
router.include_router(commodities.router, prefix="/commodities", tags=["commodities"])
router.include_router(prices.router, prefix="/prices", tags=["prices"])
router.include_router(inflation.router, prefix="/inflation", tags=["inflation"])
router.include_router(global_signals.router, prefix="/global-signals", tags=["global-signals"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
router.include_router(health_db.router, prefix="/health", tags=["health"])

# New — users & auth
router.include_router(auth_api.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])

# New — reports & notifications
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])

# New — recommendations
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

# New — AI
router.include_router(ai_context.router, prefix="/ai", tags=["ai"])

# Admin
router.include_router(admin_models.router, prefix="/admin/models", tags=["admin-models"])

# Internal — service-to-service (ml-gateway), no auth, ClusterIP only.
router.include_router(internal_models.router, prefix="/internal/models", tags=["internal"])
