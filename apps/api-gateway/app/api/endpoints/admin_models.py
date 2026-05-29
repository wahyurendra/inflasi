"""Admin endpoints for the model registry.

Spec ref: docs/INFLASI_ID_Backend_Database_Plan_Updated.md §11.3.
Mounted at /api/v1/admin/models. Requires ADMIN or GOVERNMENT_ANALYST role.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.forecast import ModelRegisterRequest, ModelRegistryRow
from app.services.model_registry import ModelRegistryService

router = APIRouter()


def _require_admin(user: dict) -> None:
    if user.get("role") not in {"ADMIN", "GOVERNMENT_ANALYST"}:
        raise HTTPException(status_code=403, detail="admin role required")


@router.get("", response_model=list[ModelRegistryRow])
async def list_models(
    model_type: str | None = Query(None),
    target_type: str | None = Query(None),
    horizon: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[ModelRegistryRow]:
    _require_admin(user)
    rows = await ModelRegistryService(db).list_models(
        model_type=model_type, target_type=target_type, horizon=horizon,
    )
    return [_row_to_schema(r) for r in rows]


@router.get("/active", response_model=list[ModelRegistryRow])
async def list_active(
    model_type: str | None = Query(None),
    target_type: str | None = Query(None),
    horizon: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[ModelRegistryRow]:
    _require_admin(user)
    rows = await ModelRegistryService(db).list_models(
        model_type=model_type, target_type=target_type,
        horizon=horizon, active_only=True,
    )
    return [_row_to_schema(r) for r in rows]


@router.post("", response_model=ModelRegistryRow)
async def register_model(
    body: ModelRegisterRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> ModelRegistryRow:
    _require_admin(user)
    row = await ModelRegistryService(db).register(**body.model_dump())
    await db.commit()
    return _row_to_schema(row)


@router.post("/{model_id}/promote", response_model=ModelRegistryRow)
async def promote_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> ModelRegistryRow:
    _require_admin(user)
    row = await ModelRegistryService(db).promote(model_id)
    if row is None:
        raise HTTPException(status_code=404, detail="model not found")
    await db.commit()
    return _row_to_schema(row)


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
