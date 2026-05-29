"""Admin endpoints for the model registry.

Spec ref: docs/INFLASI_ID_Backend_Database_Plan_Updated.md §11.3.
Mounted at /api/v1/admin/models. Requires ADMIN or GOVERNMENT_ANALYST role.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.redis import get_redis
from app.database import get_db
from app.db.repositories.model_repo import ModelRepo
from app.schemas.forecast import ModelRegisterRequest, ModelRegistryRow
from app.services.model_registry import ModelRegistryService
from app.tasks.retrain_models import SUPPORTED_MODEL_TYPES
from app.workers.forecast_batch_worker import STREAM_REQ as STREAM_FORECAST_REQ
from app.workers.retrain_worker import STREAM_REQ as STREAM_RETRAIN_REQ

router = APIRouter()


def _require_admin(user: dict) -> None:
    if user.get("role") not in {"ADMIN", "GOVERNMENT_ANALYST"}:
        raise HTTPException(status_code=403, detail="admin role required")


class BatchRunRequest(BaseModel):
    horizons: list[int] | None = Field(None, description="Defaults to 7,14,30 when omitted")
    pair_limit: int | None = Field(None, ge=1)
    concurrency: int | None = Field(None, ge=1, le=32)
    window_days: int | None = Field(None, ge=1, le=90)


class BatchRunResponse(BaseModel):
    job_id: str
    status: str
    enqueued: bool
    detail: str | None = None


class RetrainRequest(BaseModel):
    model_type: str = Field(..., description="lightgbm | prophet | sarimax | tft | ensemble")
    target_type: str = "price"
    horizon: int | None = None
    train_window_days: int | None = Field(None, ge=14)
    run_name: str | None = None
    notes: str | None = None
    dry_run: bool = False
    extra_args: list[str] | None = None


class RetrainEnqueueResponse(BaseModel):
    enqueued: bool
    stream_id: str | None = None
    detail: str | None = None


class TrainingRunRow(BaseModel):
    id: int
    run_name: str
    model_type: str
    target_type: str
    horizon: int | None = None
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    train_start_date: str | None = None
    train_end_date: str | None = None
    metrics: dict[str, Any] | None = None
    notes: str | None = None


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


# ── Batch forecast + retraining triggers ─────────────────────

@router.post("/batch-run", response_model=BatchRunResponse)
async def trigger_batch_forecast(
    body: BatchRunRequest,
    user: dict = Depends(get_current_user),
) -> BatchRunResponse:
    """Enqueue a `batch_forecast` run on the Redis stream.

    Returns 202-ish semantics: the request just publishes — the worker
    processes asynchronously. Inspect `job:batch_forecast:{job_id}` for status.
    """
    _require_admin(user)
    job_id = f"batch-{int(time.time())}-{user.get('id', 'anon')[:8]}"
    payload = {
        "job_id": job_id,
        "horizons": ",".join(str(h) for h in (body.horizons or [])),
        "pair_limit": "" if body.pair_limit is None else str(body.pair_limit),
        "concurrency": "" if body.concurrency is None else str(body.concurrency),
        "window_days": "" if body.window_days is None else str(body.window_days),
        "requested_by": user.get("id") or "anon",
    }
    try:
        redis = get_redis()
        await redis.xadd(STREAM_FORECAST_REQ, payload)
    except Exception as exc:
        return BatchRunResponse(
            job_id=job_id, status="error", enqueued=False,
            detail=f"redis unavailable: {type(exc).__name__}: {exc}",
        )
    return BatchRunResponse(job_id=job_id, status="enqueued", enqueued=True)


@router.get("/batch-run/{job_id}")
async def get_batch_run_status(
    job_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    _require_admin(user)
    redis = get_redis()
    raw = await redis.hgetall(f"job:batch_forecast:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="job not found or expired")
    return {"job_id": job_id, **raw}


@router.post("/retrain", response_model=RetrainEnqueueResponse)
async def trigger_retrain(
    body: RetrainRequest,
    user: dict = Depends(get_current_user),
) -> RetrainEnqueueResponse:
    """Enqueue a retraining run for `model_type` (and optional horizon).

    Spawns the trainer subprocess inside the api-gateway pod. Audit row is
    written to `model_training_runs`; status mirror lives in
    `job:retrain:{run_id}` once the worker picks it up.
    """
    _require_admin(user)
    if body.model_type not in SUPPORTED_MODEL_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"unsupported model_type; expected one of {sorted(SUPPORTED_MODEL_TYPES)}",
        )
    payload = {
        "model_type": body.model_type,
        "target_type": body.target_type,
        "horizon": "" if body.horizon is None else str(body.horizon),
        "train_window_days": "" if body.train_window_days is None else str(body.train_window_days),
        "run_name": body.run_name or "",
        "notes": body.notes or "",
        "dry_run": "1" if body.dry_run else "0",
        "extra_args": ",".join(body.extra_args or []),
        "requested_by": user.get("id") or "anon",
    }
    try:
        redis = get_redis()
        stream_id = await redis.xadd(STREAM_RETRAIN_REQ, payload)
    except Exception as exc:
        return RetrainEnqueueResponse(
            enqueued=False, detail=f"redis unavailable: {type(exc).__name__}: {exc}",
        )
    return RetrainEnqueueResponse(enqueued=True, stream_id=str(stream_id))


@router.get("/training-runs", response_model=list[TrainingRunRow])
async def list_training_runs(
    status: str | None = Query(None, description="RUNNING | SUCCESS | FAILED | SKIPPED"),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[TrainingRunRow]:
    _require_admin(user)
    rows = await ModelRepo(db).list_runs(status=status, limit=limit)
    return [_run_to_schema(r) for r in rows]


@router.get("/training-runs/{run_id}/job-status")
async def get_training_run_job_status(
    run_id: int,
    user: dict = Depends(get_current_user),
) -> dict:
    _require_admin(user)
    redis = get_redis()
    raw = await redis.hgetall(f"job:retrain:{run_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="job status not found or expired")
    return {"run_id": run_id, **raw}


def _run_to_schema(row) -> TrainingRunRow:
    return TrainingRunRow(
        id=row.id,
        run_name=row.run_name,
        model_type=row.model_type,
        target_type=row.target_type,
        horizon=row.horizon,
        status=row.status,
        started_at=row.started_at.isoformat() if row.started_at else None,
        finished_at=row.finished_at.isoformat() if row.finished_at else None,
        train_start_date=row.train_start_date.isoformat() if row.train_start_date else None,
        train_end_date=row.train_end_date.isoformat() if row.train_end_date else None,
        metrics=row.metrics,
        notes=row.notes,
    )
