"""Repository for `model_registry` + `model_training_runs`.

Backs the model_registry service: list/active/promote, and audit training runs.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import ModelRegistry, ModelTrainingRun


class ModelRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Registry ──────────────────────────────────────────────

    async def list(
        self,
        *,
        model_type: str | None = None,
        target_type: str | None = None,
        horizon: int | None = None,
        active_only: bool = False,
    ) -> list[ModelRegistry]:
        stmt = select(ModelRegistry)
        if model_type:
            stmt = stmt.where(ModelRegistry.model_type == model_type)
        if target_type:
            stmt = stmt.where(ModelRegistry.target_type == target_type)
        if horizon is not None:
            stmt = stmt.where(ModelRegistry.horizon == horizon)
        if active_only:
            stmt = stmt.where(ModelRegistry.is_active.is_(True))
        stmt = stmt.order_by(ModelRegistry.created_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def get(self, model_id: int) -> ModelRegistry | None:
        return (await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.id == model_id)
        )).scalar_one_or_none()

    async def get_active(
        self, *, model_type: str, target_type: str, horizon: int | None,
    ) -> ModelRegistry | None:
        stmt = select(ModelRegistry).where(and_(
            ModelRegistry.model_type == model_type,
            ModelRegistry.target_type == target_type,
            ModelRegistry.is_active.is_(True),
        ))
        if horizon is not None:
            stmt = stmt.where(ModelRegistry.horizon == horizon)
        stmt = stmt.order_by(ModelRegistry.updated_at.desc()).limit(1)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def register(
        self,
        *,
        model_name: str,
        model_type: str,
        target_type: str,
        version: str,
        artifact_path: str,
        horizon: int | None = None,
        feature_set_version: str | None = None,
        training_start_date: date | None = None,
        training_end_date: date | None = None,
        metrics: dict | None = None,
        params: dict | None = None,
        is_active: bool = False,
    ) -> ModelRegistry:
        row = ModelRegistry(
            model_name=model_name,
            model_type=model_type,
            target_type=target_type,
            horizon=horizon,
            version=version,
            artifact_path=artifact_path,
            feature_set_version=feature_set_version,
            training_start_date=training_start_date,
            training_end_date=training_end_date,
            metrics=metrics,
            params=params,
            is_active=is_active,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def promote(self, model_id: int) -> ModelRegistry | None:
        """Mark `model_id` active and deactivate every other model in its
        (model_type, target_type, horizon) slot.
        """
        target = await self.get(model_id)
        if target is None:
            return None
        await self.db.execute(
            update(ModelRegistry)
            .where(and_(
                ModelRegistry.model_type == target.model_type,
                ModelRegistry.target_type == target.target_type,
                ModelRegistry.horizon == target.horizon,
                ModelRegistry.id != model_id,
            ))
            .values(is_active=False)
        )
        target.is_active = True
        await self.db.flush()
        return target

    # ── Training runs ─────────────────────────────────────────

    async def create_run(
        self,
        *,
        run_name: str,
        model_type: str,
        target_type: str,
        horizon: int | None = None,
        params: dict | None = None,
        notes: str | None = None,
    ) -> ModelTrainingRun:
        run = ModelTrainingRun(
            run_name=run_name,
            model_type=model_type,
            target_type=target_type,
            horizon=horizon,
            params=params,
            notes=notes,
            status="RUNNING",
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def finish_run(
        self,
        *,
        run_id: int,
        status: str,
        metrics: dict | None = None,
        notes: str | None = None,
    ) -> ModelTrainingRun | None:
        run = (await self.db.execute(
            select(ModelTrainingRun).where(ModelTrainingRun.id == run_id)
        )).scalar_one_or_none()
        if run is None:
            return None
        run.status = status
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if metrics is not None:
            run.metrics = metrics
        if notes is not None:
            run.notes = notes
        await self.db.flush()
        return run

    async def list_runs(
        self, *, status: str | None = None, limit: int = 50,
    ) -> list[ModelTrainingRun]:
        stmt = select(ModelTrainingRun)
        if status:
            stmt = stmt.where(ModelTrainingRun.status == status)
        stmt = stmt.order_by(ModelTrainingRun.started_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())
