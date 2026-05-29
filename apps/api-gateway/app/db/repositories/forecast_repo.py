"""Repository for `analytics_forecast` + `forecast_model_components`.

Wraps SQLAlchemy access so services don't reach into raw SQL/ORM. Used by
`prediction_service` to persist quantile forecasts and per-model contributions.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import AnalyticsForecast, ForecastModelComponent


class ForecastRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Forecast row ──────────────────────────────────────────

    async def get(
        self, *, commodity_id: int, region_id: int, target_date: date, horizon: int,
    ) -> AnalyticsForecast | None:
        stmt = select(AnalyticsForecast).where(
            AnalyticsForecast.commodity_id == commodity_id,
            AnalyticsForecast.region_id == region_id,
            AnalyticsForecast.tanggal == target_date,
            AnalyticsForecast.horizon == horizon,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_recent(
        self,
        *,
        commodity_id: int,
        region_id: int,
        horizon: int,
        since: date,
    ) -> list[AnalyticsForecast]:
        stmt = (
            select(AnalyticsForecast)
            .where(
                AnalyticsForecast.commodity_id == commodity_id,
                AnalyticsForecast.region_id == region_id,
                AnalyticsForecast.horizon == horizon,
                AnalyticsForecast.tanggal >= since,
            )
            .order_by(AnalyticsForecast.tanggal)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def upsert(
        self,
        *,
        commodity_id: int,
        region_id: int,
        target_date: date,
        horizon: int,
        yhat: float,
        yhat_lower: float,
        yhat_upper: float,
        model_version: str,
        forecast_date: date | None = None,
        target_type: str = "price",
        p10: float | None = None,
        p50: float | None = None,
        p90: float | None = None,
        confidence_score: float | None = None,
        risk_level: str | None = None,
        top_drivers: list | dict | None = None,
        model_contribution: dict | None = None,
        prediction_interval: dict | None = None,
        model_run_id: int | None = None,
    ) -> AnalyticsForecast:
        """Insert or update a forecast row. Returns the persisted row.

        Replaces existing components on update so callers can re-write the
        ensemble breakdown without leaving stale rows behind.
        """
        existing = await self.get(
            commodity_id=commodity_id, region_id=region_id,
            target_date=target_date, horizon=horizon,
        )
        if existing:
            existing.yhat = Decimal(str(yhat))
            existing.yhat_lower = Decimal(str(yhat_lower))
            existing.yhat_upper = Decimal(str(yhat_upper))
            existing.model_version = model_version
            existing.forecast_date = forecast_date
            existing.target_date = target_date
            existing.target_type = target_type
            existing.p10 = _dec(p10)
            existing.p50 = _dec(p50)
            existing.p90 = _dec(p90)
            existing.confidence_score = _dec(confidence_score)
            existing.risk_level = risk_level
            existing.top_drivers = top_drivers
            existing.model_contribution = model_contribution
            existing.prediction_interval = prediction_interval
            existing.model_run_id = model_run_id
            await self.db.flush()
            return existing

        row = AnalyticsForecast(
            tanggal=target_date,
            region_id=region_id,
            commodity_id=commodity_id,
            horizon=horizon,
            yhat=Decimal(str(yhat)),
            yhat_lower=Decimal(str(yhat_lower)),
            yhat_upper=Decimal(str(yhat_upper)),
            model_version=model_version,
            forecast_date=forecast_date,
            target_date=target_date,
            target_type=target_type,
            p10=_dec(p10),
            p50=_dec(p50),
            p90=_dec(p90),
            confidence_score=_dec(confidence_score),
            risk_level=risk_level,
            top_drivers=top_drivers,
            model_contribution=model_contribution,
            prediction_interval=prediction_interval,
            model_run_id=model_run_id,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    # ── Components ────────────────────────────────────────────

    async def replace_components(
        self, *, forecast_id: int, components: Iterable[dict[str, Any]],
    ) -> None:
        """Wipe and rewrite per-model components for a given forecast row."""
        existing = (await self.db.execute(
            select(ForecastModelComponent).where(
                ForecastModelComponent.forecast_id == forecast_id,
            )
        )).scalars().all()
        for c in existing:
            await self.db.delete(c)
        await self.db.flush()

        for c in components:
            self.db.add(ForecastModelComponent(
                forecast_id=forecast_id,
                model_name=c["model_name"],
                model_type=c["model_type"],
                model_version=c.get("model_version"),
                prediction=_dec(c.get("prediction")),
                p10=_dec(c.get("p10")),
                p50=_dec(c.get("p50")),
                p90=_dec(c.get("p90")),
                model_weight=_dec(c.get("model_weight")),
                model_confidence=_dec(c.get("model_confidence")),
            ))
        await self.db.flush()


def _dec(v: Any) -> Decimal | None:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))
