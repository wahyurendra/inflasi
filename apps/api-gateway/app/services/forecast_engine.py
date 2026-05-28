"""Price Forecast Engine — reads `feature_store_daily`, calls ml-gateway, stores
predictions to `analytics_forecast`, and exposes them joined with ground truth.

Pipeline:
1. Load feature rows (last `history_days`) from `feature_store_daily`.
2. POST rows to ml-gateway `/forecast/predict` (multivariate, ensemble).
3. Persist horizon-specific yhat into `analytics_forecast` (one row per future
   date per horizon).

Backwards compatible: if the ml-gateway is unreachable or returns insufficient
data, falls back to a local linear forecaster so the cron continues to populate
`analytics_forecast`.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_VERSION = "ensemble-v1"
DEFAULT_HORIZONS = (7, 14, 30)


class ForecastEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Compute & store ───────────────────────────────────────

    async def forecast_commodity(
        self,
        commodity_id: int,
        region_id: int,
        horizon_days: int = 14,
        history_days: int = 90,
    ) -> list[dict]:
        """Generate price forecast for a single commodity-region pair."""
        codes = await self._resolve_codes(commodity_id, region_id)
        if not codes:
            logger.warning("commodity_id=%s / region_id=%s not in dim tables", commodity_id, region_id)
            return []
        commodity_kode, region_kode = codes

        end_date = date.today()
        start_date = end_date - timedelta(days=history_days)
        rows = await self._load_feature_rows(commodity_kode, region_kode, start_date, end_date)

        if len(rows) < 30:
            logger.warning(
                "Not enough features (rows=%s) for commodity=%s region=%s — fallback",
                len(rows), commodity_kode, region_kode,
            )
            return await self._fallback_forecast(commodity_id, region_id, horizon_days)

        horizons = sorted({horizon_days, *DEFAULT_HORIZONS})
        ml_resp = await self._call_ml_gateway(rows, horizons)
        if not ml_resp or "horizons" not in ml_resp:
            return await self._fallback_forecast(commodity_id, region_id, horizon_days)

        last_date = rows[-1]["date"]
        predictions: list[dict] = []
        for h_str, values in ml_resp["horizons"].items():
            h = int(h_str)
            for i, yhat in enumerate(values, start=1):
                predictions.append({
                    "tanggal": _to_date(last_date) + timedelta(days=i),
                    "horizon": h,
                    "yhat": round(float(yhat), 2),
                    # ml-gateway doesn't return CI yet — derive a ±10% band as placeholder.
                    "yhat_lower": round(float(yhat) * 0.90, 2),
                    "yhat_upper": round(float(yhat) * 1.10, 2),
                })

        await self._store_forecasts(commodity_id, region_id, predictions)
        # For backwards compatibility return the requested horizon slice.
        return [p for p in predictions if p["horizon"] == horizon_days]

    async def forecast_all(self, horizon_days: int = 14) -> int:
        """Run forecast for all active commodity-region pairs and store results."""
        rows = (await self.db.execute(
            text("""
                SELECT DISTINCT commodity_id, region_id
                FROM fact_price_daily
                WHERE tanggal >= :recent
            """),
            {"recent": date.today() - timedelta(days=7)},
        )).fetchall()

        count = 0
        for row in rows:
            preds = await self.forecast_commodity(row.commodity_id, row.region_id, horizon_days)
            if preds:
                count += len(preds)
        await self.db.commit()
        logger.info("Generated %s forecasts for %s pairs", count, len(rows))
        return count

    # ── Read API ──────────────────────────────────────────────

    async def get_forecast(
        self,
        commodity_id: int,
        region_id: int,
        horizon: int = 14,
    ) -> list[dict]:
        """Return forecast rows joined with ground-truth targets + observed price.

        `actual` = observed price on that date (filled when known).
        `target_h7 / h14 / h30` = supervised label (price at issue_date + horizon).
        """
        codes = await self._resolve_codes(commodity_id, region_id)
        if not codes:
            return []
        commodity_kode, region_kode = codes

        rows = (await self.db.execute(
            text("""
                SELECT af.tanggal,
                       af.yhat::float AS yhat,
                       af.yhat_lower::float AS yhat_lower,
                       af.yhat_upper::float AS yhat_upper,
                       fs.price::float AS actual,
                       fs.target_h7::float AS target_h7,
                       fs.target_h14::float AS target_h14,
                       fs.target_h30::float AS target_h30
                FROM analytics_forecast af
                LEFT JOIN feature_store_daily fs
                  ON fs.date = af.tanggal
                 AND fs.commodity_id = :ckode
                 AND fs.region_id = :rkode
                WHERE af.commodity_id = :cid
                  AND af.region_id = :rid
                  AND af.horizon = :horizon
                  AND af.tanggal >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY af.tanggal
            """),
            {
                "cid": commodity_id, "rid": region_id, "horizon": horizon,
                "ckode": commodity_kode, "rkode": region_kode,
            },
        )).mappings().all()
        return [dict(r) for r in rows]

    async def get_metrics(
        self,
        commodity_id: int,
        region_id: int,
    ) -> dict:
        """Compute MAE / RMSE / MAPE on stored forecasts vs feature_store ground truth.

        Compares `analytics_forecast.yhat` against `feature_store_daily.target_h{N}`
        observed at the forecast issue date (not the forecast target date).
        """
        codes = await self._resolve_codes(commodity_id, region_id)
        if not codes:
            return {}
        ckode, rkode = codes

        results: dict[str, Any] = {}
        for h in DEFAULT_HORIZONS:
            row = (await self.db.execute(
                text(f"""
                    SELECT
                      AVG(ABS(af.yhat::float - fs.target_h{h}::float)) AS mae,
                      SQRT(AVG(POWER(af.yhat::float - fs.target_h{h}::float, 2))) AS rmse,
                      AVG(ABS(af.yhat::float - fs.target_h{h}::float) /
                          NULLIF(fs.target_h{h}::float, 0)) * 100 AS mape
                    FROM analytics_forecast af
                    JOIN feature_store_daily fs
                      ON fs.commodity_id = :ckode AND fs.region_id = :rkode
                     AND fs.date = af.tanggal - INTERVAL '{h} days'
                    WHERE af.horizon = :h
                      AND af.commodity_id = :cid
                      AND af.region_id = :rid
                      AND fs.target_h{h} IS NOT NULL
                """),
                {"ckode": ckode, "rkode": rkode, "h": h, "cid": commodity_id, "rid": region_id},
            )).first()
            if row and row.mae is not None:
                results[f"mae_h{h}"] = round(float(row.mae), 4)
                results[f"rmse_h{h}"] = round(float(row.rmse), 4)
                results[f"mape_h{h}"] = round(float(row.mape), 4) if row.mape is not None else None
        return results

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

    async def _load_feature_rows(
        self, commodity_kode: str, region_kode: str, start: date, end: date,
    ) -> list[dict]:
        rows = (await self.db.execute(
            text("""
                SELECT *
                FROM feature_store_daily
                WHERE commodity_id = :ckode
                  AND region_id = :rkode
                  AND date BETWEEN :start AND :end
                ORDER BY date
            """),
            {"ckode": commodity_kode, "rkode": region_kode, "start": start, "end": end},
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

    async def _store_forecasts(
        self, commodity_id: int, region_id: int, predictions: list[dict],
    ) -> None:
        for pred in predictions:
            await self.db.execute(
                text("""
                    INSERT INTO analytics_forecast
                        (tanggal, region_id, commodity_id, horizon,
                         yhat, yhat_lower, yhat_upper, model_version)
                    VALUES
                        (:tanggal, :region_id, :commodity_id, :horizon,
                         :yhat, :yhat_lower, :yhat_upper, :model_version)
                    ON CONFLICT (tanggal, region_id, commodity_id, horizon)
                    DO UPDATE SET
                        yhat = EXCLUDED.yhat,
                        yhat_lower = EXCLUDED.yhat_lower,
                        yhat_upper = EXCLUDED.yhat_upper,
                        model_version = EXCLUDED.model_version
                """),
                {
                    "tanggal": pred["tanggal"],
                    "region_id": region_id,
                    "commodity_id": commodity_id,
                    "horizon": pred["horizon"],
                    "yhat": pred["yhat"],
                    "yhat_lower": pred["yhat_lower"],
                    "yhat_upper": pred["yhat_upper"],
                    "model_version": MODEL_VERSION,
                },
            )

    async def _fallback_forecast(
        self, commodity_id: int, region_id: int, horizon_days: int,
    ) -> list[dict]:
        """Local linear forecast from raw prices when ml-gateway/features unavailable."""
        import statistics

        rows = (await self.db.execute(
            text("""
                SELECT tanggal, harga::float AS harga
                FROM fact_price_daily
                WHERE commodity_id = :cid AND region_id = :rid
                  AND tanggal >= :start
                ORDER BY tanggal
            """),
            {"cid": commodity_id, "rid": region_id, "start": date.today() - timedelta(days=30)},
        )).fetchall()
        if len(rows) < 5:
            return []

        prices = [float(r.harga) for r in rows]
        last_date = rows[-1].tanggal
        recent = prices[-14:] if len(prices) >= 14 else prices
        daily_change = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
        try:
            std = statistics.stdev(recent)
        except statistics.StatisticsError:
            std = 0.0

        predictions = []
        for i in range(1, horizon_days + 1):
            yhat = prices[-1] + daily_change * i
            predictions.append({
                "tanggal": last_date + timedelta(days=i),
                "horizon": horizon_days,
                "yhat": round(yhat, 2),
                "yhat_lower": round(yhat - 1.5 * std, 2),
                "yhat_upper": round(yhat + 1.5 * std, 2),
            })
        await self._store_forecasts(commodity_id, region_id, predictions)
        return predictions


def _serialize_row(row: dict) -> dict:
    """Make a feature row JSON-friendly: dates → iso, Decimal → float."""
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
