"""Internal model registry lookup for ml-gateway (no auth).

The admin-facing equivalent at ``/admin/models/active`` requires a Firebase ID
token + ADMIN role — ml-gateway has neither (it's a service-to-service caller
on the cluster network). This endpoint mirrors the same read-only query without
the auth gate.

Mounted at ``/api/internal/models/active``. Only exposed on the ClusterIP
Service for inflasi-api; never reachable from the public Traefik ingress.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.model_registry import ModelRegistryService

router = APIRouter()


@router.get("/active")
async def get_active_model(
    model_type: str = Query(..., description="lightgbm | prophet | sarimax | tft | ensemble | stacking"),
    target_type: str = Query("price"),
    horizon: int | None = Query(None, description="Required for horizon-scoped models (lightgbm/tft)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the single active model row for the given slot.

    Returns 404 when no active model is registered; callers should treat that as
    "this model isn't available yet" and degrade gracefully.
    """
    active = await ModelRegistryService(db).resolve_active(
        model_type=model_type, target_type=target_type, horizon=horizon,
    )
    if active is None:
        raise HTTPException(
            status_code=404,
            detail=f"no active model for {model_type}/{target_type}/h={horizon}",
        )
    return {
        "id": active.id,
        "model_name": active.model_name,
        "model_type": active.model_type,
        "target_type": active.target_type,
        "horizon": active.horizon,
        "version": active.version,
        "artifact_path": active.artifact_path,
    }
