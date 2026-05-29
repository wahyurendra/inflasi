"""Prediction service — single entry point for the forecast endpoint.

Pipeline:
  1. Resolve dim codes for (commodity_id, region_id).
  2. Load latest `feature_store_daily` window.
  3. Call ml-gateway `/forecast/predict`.
  4. Compute quantile band + risk level + top drivers (heuristic until the ML
     gateway returns native quantiles).
  5. Persist to `analytics_forecast` + `forecast_model_components` via repos.
  6. Stamp the active model version from `model_registry` when registered.

Components-per-base-model are derived from the ml-gateway's `models_used` map
and the ensemble's published weights. Once the ML side returns native quantiles
and per-model series this becomes pass-through.
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.repositories.forecast_repo import ForecastRepo
from app.services.model_registry import ModelRegistryService

logger = logging.getLogger(__name__)

DEFAULT_HORIZONS = (7, 14, 30)
DEFAULT_INFLATION_HORIZONS = (1, 3, 6)
ENSEMBLE_WEIGHTS = {"arima": 0.3, "prophet": 0.3, "tft": 0.4}
_MIN_ROWS = 30
_HISTORY_DAYS = 90
_MONTHLY_MIN_ROWS = 12
_MONTHLY_HISTORY_MONTHS = 36


@dataclass
class ForecastPoint:
    target_date: date
    horizon: int
    yhat: float
    yhat_lower: float
    yhat_upper: float
    p10: float
    p50: float
    p90: float
    confidence_score: float
    risk_level: str
    top_drivers: list[dict[str, Any]] = field(default_factory=list)
    model_contribution: dict[str, float] = field(default_factory=dict)
    components: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class InflationForecastPoint:
    target_date: date  # first day of the target month
    horizon_months: int
    yhat: float        # forecasted monthly inflation (% mom)
    p10: float
    p50: float
    p90: float
    confidence_score: float
    risk_level: str
    top_drivers: list[dict[str, Any]] = field(default_factory=list)
    model_contribution: dict[str, float] = field(default_factory=dict)
    components: list[dict[str, Any]] = field(default_factory=list)


class PredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ForecastRepo(db)
        self.registry = ModelRegistryService(db)

    async def forecast_pair(
        self,
        *,
        commodity_id: int,
        region_id: int,
        horizon: int,
        persist: bool = True,
    ) -> list[ForecastPoint]:
        """Forecast a single commodity-region pair for one horizon.

        Returns the horizon's slice of predictions. When `persist=True`, every
        prediction in the slice is upserted to analytics_forecast with components.
        """
        codes = await self._resolve_codes(commodity_id, region_id)
        if codes is None:
            return []
        commodity_kode, region_kode = codes

        rows = await self._load_features(commodity_kode, region_kode)
        if len(rows) < _MIN_ROWS:
            logger.info(
                "fallback: insufficient features (%s) for c=%s r=%s",
                len(rows), commodity_kode, region_kode,
            )
            return await self._fallback(
                commodity_id, region_id, horizon, persist=persist,
            )

        horizons = sorted({horizon, *DEFAULT_HORIZONS})
        ml_resp = await self._call_ml_gateway(rows, horizons)
        if not ml_resp or "horizons" not in ml_resp:
            return await self._fallback(
                commodity_id, region_id, horizon, persist=persist,
            )

        last_known_price = float(rows[-1].get("price") or 0.0) or None
        recent_std = _rolling_std([r.get("price") for r in rows[-30:]])
        last_date = _to_date(rows[-1]["date"])

        version = await self.registry.version_label(
            model_type="ensemble", target_type="price", horizon=horizon,
        )

        # Prefer ml-gateway's native quantiles + per-model components when present.
        ml_quantiles = (ml_resp.get("quantiles") or {}).get(str(horizon)) or {}
        ml_components = (ml_resp.get("components") or {}).get(str(horizon)) or {}
        ml_weights = ml_resp.get("weights") or {}
        models_used = ml_resp.get("models_used") or {}

        forecast_issue = date.today()
        points: list[ForecastPoint] = []
        for h_str, values in ml_resp["horizons"].items():
            h = int(h_str)
            if h != horizon:
                continue
            for offset, yhat in enumerate(values, start=1):
                yhat_f = float(yhat)
                target_date = last_date + timedelta(days=offset)

                p10, p50, p90 = _pick_quantiles(ml_quantiles, offset - 1, yhat_f, recent_std)
                contribution = _contribution_from_weights(ml_weights) \
                    or _model_contribution(models_used)
                components = _components_from_ml(
                    ml_components, offset - 1, contribution, version,
                ) or _component_rows(models_used, yhat_f, version)

                pt = ForecastPoint(
                    target_date=target_date,
                    horizon=h,
                    yhat=yhat_f,
                    yhat_lower=p10,
                    yhat_upper=p90,
                    p10=p10, p50=p50, p90=p90,
                    confidence_score=_confidence(recent_std, last_known_price, h),
                    risk_level=_risk_level(yhat_f, last_known_price),
                    top_drivers=_top_drivers(rows),
                    model_contribution=contribution,
                    components=components,
                )
                points.append(pt)

        if persist:
            for pt in points:
                row = await self.repo.upsert(
                    commodity_id=commodity_id,
                    region_id=region_id,
                    target_date=pt.target_date,
                    horizon=pt.horizon,
                    yhat=pt.yhat,
                    yhat_lower=pt.yhat_lower,
                    yhat_upper=pt.yhat_upper,
                    model_version=version,
                    forecast_date=forecast_issue,
                    target_type="price",
                    p10=pt.p10, p50=pt.p50, p90=pt.p90,
                    confidence_score=pt.confidence_score,
                    risk_level=pt.risk_level,
                    top_drivers=pt.top_drivers,
                    model_contribution=pt.model_contribution,
                    prediction_interval={"lower": pt.yhat_lower, "upper": pt.yhat_upper},
                )
                await self.repo.replace_components(
                    forecast_id=row.id, components=pt.components,
                )
        return points

    async def forecast_pair_all_horizons(
        self,
        *,
        commodity_id: int,
        region_id: int,
    ) -> list[ForecastPoint]:
        """Forecast (commodity, region) for every horizon in DEFAULT_HORIZONS.

        Single ml-gateway round-trip; persists points for h=7, 14, 30. Used by
        the refresh worker so we don't pay 3x ml-gateway cost per pair.
        """
        codes = await self._resolve_codes(commodity_id, region_id)
        if codes is None:
            return []
        commodity_kode, region_kode = codes

        rows = await self._load_features(commodity_kode, region_kode)
        if len(rows) < _MIN_ROWS:
            logger.info(
                "fallback: insufficient features (%s) for c=%s r=%s",
                len(rows), commodity_kode, region_kode,
            )
            out: list[ForecastPoint] = []
            for h in DEFAULT_HORIZONS:
                out.extend(await self._fallback(
                    commodity_id, region_id, h, persist=True,
                ))
            return out

        horizons: list[int] = sorted(int(h) for h in DEFAULT_HORIZONS)
        ml_resp = await self._call_ml_gateway(rows, horizons)
        if not ml_resp or "horizons" not in ml_resp:
            out = []
            for h in DEFAULT_HORIZONS:
                out.extend(await self._fallback(
                    commodity_id, region_id, h, persist=True,
                ))
            return out

        last_known_price = float(rows[-1].get("price") or 0.0) or None
        recent_std = _rolling_std([r.get("price") for r in rows[-30:]])
        last_date = _to_date(rows[-1]["date"])
        forecast_issue = date.today()

        ml_components_all = ml_resp.get("components") or {}
        ml_quantiles_all = ml_resp.get("quantiles") or {}
        ml_weights = ml_resp.get("weights") or {}
        models_used = ml_resp.get("models_used") or {}

        all_points: list[ForecastPoint] = []
        for h_str, values in ml_resp["horizons"].items():
            h = int(h_str)
            if h not in DEFAULT_HORIZONS:
                continue
            version = await self.registry.version_label(
                model_type="ensemble", target_type="price", horizon=h,
            )
            ml_quantiles = ml_quantiles_all.get(str(h)) or {}
            ml_components = ml_components_all.get(str(h)) or {}

            for offset, yhat in enumerate(values, start=1):
                yhat_f = float(yhat)
                target_date = last_date + timedelta(days=offset)
                p10, p50, p90 = _pick_quantiles(ml_quantiles, offset - 1, yhat_f, recent_std)
                contribution = _contribution_from_weights(ml_weights) \
                    or _model_contribution(models_used)
                components = _components_from_ml(
                    ml_components, offset - 1, contribution, version,
                ) or _component_rows(models_used, yhat_f, version)

                pt = ForecastPoint(
                    target_date=target_date,
                    horizon=h,
                    yhat=yhat_f,
                    yhat_lower=p10,
                    yhat_upper=p90,
                    p10=p10, p50=p50, p90=p90,
                    confidence_score=_confidence(recent_std, last_known_price, h),
                    risk_level=_risk_level(yhat_f, last_known_price),
                    top_drivers=_top_drivers(rows),
                    model_contribution=contribution,
                    components=components,
                )
                all_points.append(pt)

                row = await self.repo.upsert(
                    commodity_id=commodity_id,
                    region_id=region_id,
                    target_date=pt.target_date,
                    horizon=pt.horizon,
                    yhat=pt.yhat,
                    yhat_lower=pt.yhat_lower,
                    yhat_upper=pt.yhat_upper,
                    model_version=version,
                    forecast_date=forecast_issue,
                    target_type="price",
                    p10=pt.p10, p50=pt.p50, p90=pt.p90,
                    confidence_score=pt.confidence_score,
                    risk_level=pt.risk_level,
                    top_drivers=pt.top_drivers,
                    model_contribution=pt.model_contribution,
                    prediction_interval={"lower": pt.yhat_lower, "upper": pt.yhat_upper},
                )
                await self.repo.replace_components(
                    forecast_id=row.id, components=pt.components,
                )
        return all_points

    async def predict_inflation(
        self,
        *,
        region_id: int,
        horizons: list[int] | None = None,
        persist: bool = True,
    ) -> list[InflationForecastPoint]:
        """Monthly inflation forecast for a region across the requested horizons.

        Reads the recent window of `feature_store_monthly`, calls the ml-gateway's
        `/inflation/predict`, and persists each horizon's point + p10/p50/p90 to
        `analytics_forecast` with `target_type='inflation'` and a synthetic
        `commodity_id=0` (inflation is region-scoped, not commodity-scoped).
        """
        horizons = sorted(set(int(h) for h in (horizons or DEFAULT_INFLATION_HORIZONS)))
        rows = await self._load_monthly_features(region_id)
        if len(rows) < _MONTHLY_MIN_ROWS:
            logger.info(
                "inflation forecast: insufficient monthly features (%s) for region=%s",
                len(rows), region_id,
            )
            return []

        ml_resp = await self._call_ml_inflation(rows, horizons)
        if not ml_resp or "horizons" not in ml_resp:
            return []

        last_period = _to_date(rows[-1]["period"])
        last_actual = _safe_float(rows[-1].get("inflasi_mtm"))
        recent_std = _rolling_std(
            [r.get("inflasi_mtm") for r in rows[-12:]],
        )

        version = await self.registry.version_label(
            model_type="ensemble", target_type="inflation", horizon=None,
        )
        ml_components = ml_resp.get("components") or {}
        ml_quantiles = ml_resp.get("quantiles") or {}
        ml_weights = ml_resp.get("weights") or {}
        models_used = ml_resp.get("models_used") or {}
        forecast_issue = date.today()

        points: list[InflationForecastPoint] = []
        for h in horizons:
            point_val = ml_resp["horizons"].get(str(h))
            if point_val is None:
                continue
            yhat = float(point_val)
            target_d = _shift_months(last_period, h)
            quantiles = ml_quantiles.get(str(h)) or {}
            p10 = _opt_float(quantiles.get("p10"), default=yhat - 1.2816 * recent_std)
            p50 = _opt_float(quantiles.get("p50"), default=yhat)
            p90 = _opt_float(quantiles.get("p90"), default=yhat + 1.2816 * recent_std)
            contribution = _contribution_from_weights(ml_weights) \
                or _model_contribution(models_used)
            components = _components_from_inflation_ml(
                ml_components.get(str(h)) or {}, contribution, version,
            )

            pt = InflationForecastPoint(
                target_date=target_d,
                horizon_months=h,
                yhat=round(yhat, 4),
                p10=round(p10, 4),
                p50=round(p50, 4),
                p90=round(p90, 4),
                confidence_score=_confidence(recent_std, last_actual, h * 30),
                risk_level=_inflation_risk_level(yhat),
                top_drivers=_inflation_drivers(rows),
                model_contribution=contribution,
                components=components,
            )
            points.append(pt)

        if persist:
            for pt in points:
                row = await self.repo.upsert(
                    commodity_id=0,
                    region_id=region_id,
                    target_date=pt.target_date,
                    horizon=pt.horizon_months,
                    yhat=pt.yhat,
                    yhat_lower=pt.p10,
                    yhat_upper=pt.p90,
                    model_version=version,
                    forecast_date=forecast_issue,
                    target_type="inflation",
                    p10=pt.p10, p50=pt.p50, p90=pt.p90,
                    confidence_score=pt.confidence_score,
                    risk_level=pt.risk_level,
                    top_drivers=pt.top_drivers,
                    model_contribution=pt.model_contribution,
                    prediction_interval={"lower": pt.p10, "upper": pt.p90},
                )
                await self.repo.replace_components(
                    forecast_id=row.id, components=pt.components,
                )
        return points

    async def _load_monthly_features(self, region_id: int) -> list[dict]:
        rows = (await self.db.execute(
            text("""
                SELECT *
                FROM feature_store_monthly
                WHERE region_id = :region_id
                ORDER BY period
                LIMIT :limit
            """),
            {"region_id": region_id, "limit": _MONTHLY_HISTORY_MONTHS},
        )).mappings().all()
        return [dict(r) for r in rows]

    async def _call_ml_inflation(
        self, rows: list[dict], horizons: list[int],
    ) -> dict | None:
        payload = {
            "features": [_serialize_row(r) for r in rows],
            "horizons": horizons,
            "model": "ensemble",
        }
        url = f"{settings.ml_gateway_url.rstrip('/')}/inflation/predict"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception:
            logger.exception("ml-gateway /inflation/predict failed")
            return None

    async def forecast_all(self, horizon: int) -> int:
        """Run prediction for every commodity-region pair seen in the last week."""
        rows = (await self.db.execute(
            text("""
                SELECT DISTINCT commodity_id, region_id
                FROM fact_price_daily
                WHERE tanggal >= :recent
            """),
            {"recent": date.today() - timedelta(days=7)},
        )).fetchall()

        total = 0
        for r in rows:
            points = await self.forecast_pair(
                commodity_id=r.commodity_id, region_id=r.region_id, horizon=horizon,
            )
            total += len(points)
        await self.db.commit()
        return total

    # ── Internals ─────────────────────────────────────────────

    async def _resolve_codes(self, commodity_id: int, region_id: int) -> tuple[str, str] | None:
        row = (await self.db.execute(
            text("""
                SELECT
                  (SELECT kode_komoditas FROM dim_commodity WHERE id = :cid) AS ckode,
                  (SELECT kode_wilayah FROM dim_region WHERE id = :rid) AS rkode
            """),
            {"cid": commodity_id, "rid": region_id},
        )).first()
        if not row or not row.ckode or not row.rkode:
            return None
        return row.ckode, row.rkode

    async def _load_features(self, commodity_kode: str, region_kode: str) -> list[dict]:
        start = date.today() - timedelta(days=_HISTORY_DAYS)
        rows = (await self.db.execute(
            text("""
                SELECT *
                FROM feature_store_daily
                WHERE commodity_id = :ckode
                  AND region_id = :rkode
                  AND date BETWEEN :start AND :end
                ORDER BY date
            """),
            {"ckode": commodity_kode, "rkode": region_kode,
             "start": start, "end": date.today()},
        )).mappings().all()
        return [dict(r) for r in rows]

    async def _call_ml_gateway(self, rows: list[dict], horizons: list[int]) -> dict | None:
        payload = {
            "features": [_serialize_row(r) for r in rows],
            "horizons": horizons,
            "model": "ensemble",
        }
        url = f"{settings.ml_gateway_url.rstrip('/')}/forecast/predict"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception:
            logger.exception("ml-gateway /forecast/predict failed")
            return None

    async def _fallback(
        self, commodity_id: int, region_id: int, horizon: int, *, persist: bool,
    ) -> list[ForecastPoint]:
        rows = (await self.db.execute(
            text("""
                SELECT tanggal, harga::float AS harga
                FROM fact_price_daily
                WHERE commodity_id = :cid AND region_id = :rid
                  AND tanggal >= :start
                ORDER BY tanggal
            """),
            {"cid": commodity_id, "rid": region_id,
             "start": date.today() - timedelta(days=30)},
        )).fetchall()
        if len(rows) < 5:
            return []

        prices = [float(r.harga) for r in rows]
        last_date_val = rows[-1].tanggal
        recent = prices[-14:] if len(prices) >= 14 else prices
        daily_change = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
        try:
            std = statistics.stdev(recent)
        except statistics.StatisticsError:
            std = 0.0

        version = await self.registry.version_label(
            model_type="fallback", target_type="price", horizon=horizon,
        )
        forecast_issue = date.today()

        points: list[ForecastPoint] = []
        for i in range(1, horizon + 1):
            yhat = prices[-1] + daily_change * i
            p10, p50, p90 = yhat - 1.5 * std, yhat, yhat + 1.5 * std
            target_d = last_date_val + timedelta(days=i)
            points.append(ForecastPoint(
                target_date=target_d,
                horizon=horizon,
                yhat=round(yhat, 2),
                yhat_lower=round(p10, 2),
                yhat_upper=round(p90, 2),
                p10=round(p10, 2),
                p50=round(p50, 2),
                p90=round(p90, 2),
                confidence_score=_confidence(std, prices[-1], horizon),
                risk_level=_risk_level(yhat, prices[-1]),
                top_drivers=[{"feature": "fallback_trend", "impact": round(daily_change, 4)}],
                model_contribution={"fallback_linear": 1.0},
                components=[{
                    "model_name": "fallback_linear", "model_type": "linear",
                    "model_version": version, "prediction": round(yhat, 2),
                    "p10": round(p10, 2), "p50": round(p50, 2), "p90": round(p90, 2),
                    "model_weight": 1.0, "model_confidence": 0.3,
                }],
            ))

        if persist:
            for pt in points:
                row = await self.repo.upsert(
                    commodity_id=commodity_id,
                    region_id=region_id,
                    target_date=pt.target_date,
                    horizon=pt.horizon,
                    yhat=pt.yhat,
                    yhat_lower=pt.yhat_lower,
                    yhat_upper=pt.yhat_upper,
                    model_version=version,
                    forecast_date=forecast_issue,
                    target_type="price",
                    p10=pt.p10, p50=pt.p50, p90=pt.p90,
                    confidence_score=pt.confidence_score,
                    risk_level=pt.risk_level,
                    top_drivers=pt.top_drivers,
                    model_contribution=pt.model_contribution,
                    prediction_interval={"lower": pt.yhat_lower, "upper": pt.yhat_upper},
                )
                await self.repo.replace_components(
                    forecast_id=row.id, components=pt.components,
                )
        return points


# ── Helpers ──────────────────────────────────────────────────

def _rolling_std(prices: list[Any]) -> float:
    nums = [float(p) for p in prices if p is not None]
    if len(nums) < 2:
        return 0.0
    try:
        return statistics.stdev(nums)
    except statistics.StatisticsError:
        return 0.0


def _pick_quantiles(
    ml_quantiles: dict, index: int, yhat: float, std: float,
) -> tuple[float, float, float]:
    """Use ml-gateway quantiles for `index` when present; otherwise approximate."""
    p10_arr = ml_quantiles.get("p10") or []
    p50_arr = ml_quantiles.get("p50") or []
    p90_arr = ml_quantiles.get("p90") or []
    if 0 <= index < len(p10_arr) and index < len(p90_arr):
        return (
            float(p10_arr[index]),
            float(p50_arr[index]) if index < len(p50_arr) else yhat,
            float(p90_arr[index]),
        )
    band = 1.2816 * std * math.sqrt(max(index + 1, 1))  # 80% interval ≈ ±1.28σ
    return round(yhat - band, 2), round(yhat, 2), round(yhat + band, 2)


def _contribution_from_weights(weights: dict[str, float]) -> dict[str, float]:
    """Renormalize ml-gateway's reported weights over active models."""
    if not weights:
        return {}
    total = sum(weights.values()) or 1.0
    return {k: round(v / total, 4) for k, v in weights.items()}


def _components_from_ml(
    ml_components: dict[str, list[float]],
    index: int,
    contribution: dict[str, float],
    version: str,
) -> list[dict[str, Any]]:
    """Build component rows from ml-gateway's per-model series at `index`."""
    if not ml_components:
        return []
    out: list[dict[str, Any]] = []
    for name, series in ml_components.items():
        if index >= len(series):
            continue
        pred = float(series[index])
        out.append({
            "model_name": name,
            "model_type": name,
            "model_version": version,
            "prediction": round(pred, 2),
            "p10": None,
            "p50": round(pred, 2),
            "p90": None,
            "model_weight": contribution.get(name),
            "model_confidence": None,
        })
    return out


def _confidence(std: float, last_price: float | None, horizon: int) -> float:
    """Cheap confidence proxy in [0, 1]: shrinks with volatility and horizon."""
    if not last_price or last_price <= 0:
        return 0.5
    cv = std / last_price if last_price else 1.0  # coefficient of variation
    base = max(0.0, min(1.0, 1.0 - cv * 2))
    decay = max(0.4, 1.0 - 0.01 * horizon)
    return round(base * decay, 4)


def _risk_level(yhat: float, last_price: float | None) -> str:
    if not last_price or last_price <= 0:
        return "unknown"
    change = (yhat - last_price) / last_price
    if change >= 0.10:
        return "high"
    if change >= 0.05:
        return "medium"
    if change <= -0.10:
        return "high"
    return "low"


def _top_drivers(rows: list[dict]) -> list[dict[str, Any]]:
    """Pick a handful of populated feature columns from the latest row.

    Until SHAP/permutation importance comes back from ml-gateway, surfacing the
    populated regressor names gives the dashboard something honest to render.
    """
    if not rows:
        return []
    candidate_cols = (
        "price_lag_7", "price_lag_14", "rolling_mean_30",
        "rainfall_anomaly", "lebaran_minus_7", "ramadan_flag", "usd_idr_change",
    )
    last = rows[-1]
    drivers: list[dict[str, Any]] = []
    for col in candidate_cols:
        if col in last and last[col] is not None:
            try:
                drivers.append({"feature": col, "impact": round(float(last[col]), 4)})
            except (TypeError, ValueError):
                continue
        if len(drivers) >= 4:
            break
    return drivers


def _model_contribution(models_used: dict[str, bool]) -> dict[str, float]:
    """Renormalize ensemble weights over the successfully-used base models."""
    active = [k for k, v in models_used.items() if v]
    if not active:
        return {}
    total = sum(ENSEMBLE_WEIGHTS.get(k, 1.0) for k in active)
    return {k: round(ENSEMBLE_WEIGHTS.get(k, 1.0) / total, 4) for k in active}


def _component_rows(
    models_used: dict[str, bool], yhat: float, version: str,
) -> list[dict[str, Any]]:
    """Per-model component rows derived from the ensemble weights.

    Approximate until ml-gateway returns per-model series; each used base model
    is recorded with its renormalized weight and the ensemble's yhat as proxy.
    """
    contribution = _model_contribution(models_used)
    return [
        {
            "model_name": name, "model_type": name, "model_version": version,
            "prediction": round(yhat, 2),
            "p10": None, "p50": round(yhat, 2), "p90": None,
            "model_weight": weight, "model_confidence": None,
        }
        for name, weight in contribution.items()
    ]


def _serialize_row(row: dict) -> dict:
    """Make a feature row JSON-friendly for ml-gateway POST."""
    from decimal import Decimal
    out: dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, date):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, bool):
            out[k] = int(v)
        else:
            out[k] = v
    return out


def _to_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"cannot coerce {value!r} to date")


def _shift_months(d: date, months: int) -> date:
    """Add `months` to the first day of `d`'s month."""
    month_index = d.year * 12 + (d.month - 1) + months
    year, month0 = divmod(month_index, 12)
    return date(year, month0 + 1, 1)


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _opt_float(v: Any, *, default: float) -> float:
    f = _safe_float(v)
    return f if f is not None else default


def _inflation_risk_level(yhat: float) -> str:
    """Coarse risk bucket on monthly inflation (% mom)."""
    if yhat >= 1.0:
        return "high"
    if yhat >= 0.5:
        return "medium"
    if yhat <= -0.5:
        return "high"
    return "low"


def _inflation_drivers(rows: list[dict]) -> list[dict[str, Any]]:
    """Surface a handful of populated monthly feature columns."""
    if not rows:
        return []
    last = rows[-1]
    candidates = (
        "food_price_change_mom", "kurs_change_mom", "bbm_change_mom",
        "rainfall_anomaly", "ramadan_flag", "lebaran_flag", "harvest_flag",
    )
    drivers: list[dict[str, Any]] = []
    for col in candidates:
        v = last.get(col)
        if v is None:
            continue
        try:
            drivers.append({"feature": col, "impact": round(float(v), 4)})
        except (TypeError, ValueError):
            continue
        if len(drivers) >= 4:
            break
    return drivers


def _components_from_inflation_ml(
    per_model: dict[str, float],
    contribution: dict[str, float],
    version: str,
) -> list[dict[str, Any]]:
    if not per_model:
        return []
    out: list[dict[str, Any]] = []
    for name, pred in per_model.items():
        try:
            p = float(pred)
        except (TypeError, ValueError):
            continue
        out.append({
            "model_name": name,
            "model_type": name,
            "model_version": version,
            "prediction": round(p, 6),
            "p10": None,
            "p50": round(p, 6),
            "p90": None,
            "model_weight": contribution.get(name),
            "model_confidence": None,
        })
    return out
