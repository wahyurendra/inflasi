"""Internal model registry endpoints for trusted in-cluster workloads.

Active-model lookup is read-only and unauthenticated for the ML Gateway. Model
registration is a write operation and requires ``X-Training-Token`` shared by
the API Gateway and training Jobs through a Kubernetes Secret.

Mounted at ``/api/internal/models/active``. Only exposed on the ClusterIP
Service for inflasi-api; never reachable from the public Traefik ingress.
"""

from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.forecast import ModelRegisterRequest, ModelRegistryRow
from app.services.model_registry import ModelRegistryService

router = APIRouter()


def _require_training_token(received: str | None) -> None:
    """Authenticate a training Job without a short-lived Firebase user token."""
    expected = os.environ.get("TRAINING_SERVICE_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(
            status_code=503,
            detail="training service authentication is not configured",
        )
    if not received or not hmac.compare_digest(received, expected):
        raise HTTPException(status_code=401, detail="invalid training service token")


def _row_to_schema(row) -> ModelRegistryRow:
    return ModelRegistryRow(
        id=row.id,
        model_name=row.model_name,
        model_type=row.model_type,
        target_type=row.target_type,
        horizon=row.horizon,
        version=row.version,
        artifact_path=row.artifact_path,
        feature_set_version=row.feature_set_version,
        is_active=row.is_active,
        metrics=row.metrics,
        params=row.params,
    )


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


@router.post("", response_model=ModelRegistryRow)
async def register_model_from_training(
    body: ModelRegisterRequest,
    x_training_token: str | None = Header(None, alias="X-Training-Token"),
    db: AsyncSession = Depends(get_db),
) -> ModelRegistryRow:
    """Register an artifact produced by a Kubernetes training Job."""
    _require_training_token(x_training_token)
    row = await ModelRegistryService(db).register(**body.model_dump())
    await db.commit()
    return _row_to_schema(row)
