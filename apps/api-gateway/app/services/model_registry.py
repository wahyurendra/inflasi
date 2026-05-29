"""Model registry service — selects the active model for a (type, target, horizon)
slot and exposes registration/promotion. Thin wrapper around ModelRepo so endpoints
and prediction_service don't reach into ORM directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.model_repo import ModelRepo
from app.models.tables import ModelRegistry


@dataclass
class ActiveModel:
    """Snapshot of an active registry row, copied so callers can keep using it
    after the session is gone (relevant for response objects)."""
    id: int
    model_name: str
    model_type: str
    target_type: str
    horizon: int | None
    version: str
    artifact_path: str
    metrics: dict | None

    @classmethod
    def from_row(cls, row: ModelRegistry) -> "ActiveModel":
        return cls(
            id=row.id,
            model_name=row.model_name,
            model_type=row.model_type,
            target_type=row.target_type,
            horizon=row.horizon,
            version=row.version,
            artifact_path=row.artifact_path,
            metrics=row.metrics,
        )


class ModelRegistryService:
    DEFAULT_VERSION = "ensemble-v1-fallback"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ModelRepo(db)

    async def resolve_active(
        self, *, model_type: str, target_type: str, horizon: int | None,
    ) -> ActiveModel | None:
        row = await self.repo.get_active(
            model_type=model_type, target_type=target_type, horizon=horizon,
        )
        return ActiveModel.from_row(row) if row else None

    async def version_label(
        self, *, model_type: str, target_type: str, horizon: int | None,
    ) -> str:
        """Resolve the version string to stamp on a forecast — falls back to a
        deterministic placeholder when no model is registered yet."""
        active = await self.resolve_active(
            model_type=model_type, target_type=target_type, horizon=horizon,
        )
        return active.version if active else self.DEFAULT_VERSION

    async def list_models(
        self,
        *,
        model_type: str | None = None,
        target_type: str | None = None,
        horizon: int | None = None,
        active_only: bool = False,
    ) -> list[ModelRegistry]:
        return await self.repo.list(
            model_type=model_type, target_type=target_type,
            horizon=horizon, active_only=active_only,
        )

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
        return await self.repo.register(
            model_name=model_name, model_type=model_type, target_type=target_type,
            version=version, artifact_path=artifact_path, horizon=horizon,
            feature_set_version=feature_set_version,
            training_start_date=training_start_date,
            training_end_date=training_end_date,
            metrics=metrics, params=params, is_active=is_active,
        )

    async def promote(self, model_id: int) -> ModelRegistry | None:
        return await self.repo.promote(model_id)
