"""Evaluate stored forecasts against the actuals that have since arrived.

Walks `analytics_forecast` rows whose `target_date` is already in the past,
joins them to `fact_price_daily` for the matching (commodity, region, date),
and computes a small basket of error metrics per (model_version, horizon).

Two surfaces:

* `ForecastMonitor.evaluate_window` — compute metrics across a date window
  and persist a summary row into `forecast_backtest_results`. Used by the
  `evaluate_forecasts` task that runs after the daily price ETL.
* `ForecastMonitor.metrics_by_model` — read-only query used by
  `GET /analytics/model-performance` to render the dashboard chart.

Drift detection is intentionally cheap: we compare the recent 7-day MAPE
against the trailing 30-day baseline and emit a single boolean flag.
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("forecast_monitor")

_DEFAULT_WINDOW_DAYS = 30
_DRIFT_RECENT_DAYS = 7
_DRIFT_BASELINE_DAYS = 30
_DRIFT_RATIO_THRESHOLD = 1.5  # 50% degradation flags drift


@dataclass
class HorizonMetrics:
    model_version: str
    horizon: int
    target_type: str
    n: int
    mae: float
    mape: float
    coverage_p10_p90: float
    drift_flag: bool


class ForecastMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_window(
        self,
        *,
        window_days: int = _DEFAULT_WINDOW_DAYS,
        target_type: str = "price",
    ) -> list[HorizonMetrics]:
        """Compute and persist forecast vs actual metrics over a window.

        Returns the per-(model, horizon) metrics; persists them as
        `forecast_backtest_results` rows so the dashboard / analytics endpoints
        can read a historical timeline.
        """
        end = date.today()
        start = end - timedelta(days=window_days)

        rows = await self._join_actuals(start=start, end=end, target_type=target_type)
        if not rows:
            return []

        by_key: dict[tuple[str, int], list[dict]] = {}
        for r in rows:
            key = (r["model_version"] or "unknown", int(r["horizon"]))
            by_key.setdefault(key, []).append(r)

        recent_cutoff = end - timedelta(days=_DRIFT_RECENT_DAYS)
        out: list[HorizonMetrics] = []
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        for (version, horizon), pairs in by_key.items():
            metrics = _aggregate(pairs)
            recent = [p for p in pairs if p["target_date"] >= recent_cutoff]
            baseline_cutoff = end - timedelta(days=_DRIFT_BASELINE_DAYS)
            baseline = [p for p in pairs if p["target_date"] >= baseline_cutoff]
            drift = _drift_flag(recent, baseline)

            hm = HorizonMetrics(
                model_version=version,
                horizon=horizon,
                target_type=target_type,
                n=metrics["n"],
                mae=metrics["mae"],
                mape=metrics["mape"],
                coverage_p10_p90=metrics["coverage"],
                drift_flag=drift,
            )
            out.append(hm)
            await self._persist_backtest(hm, start, end, now_naive)

        await self.db.commit()
        logger.info("forecast monitor: evaluated %s (version, horizon) slots", len(out))
        return out

    async def metrics_by_model(
        self,
        *,
        window_days: int = _DEFAULT_WINDOW_DAYS,
        target_type: str = "price",
    ) -> list[dict]:
        """Read-only view for the model-performance dashboard endpoint."""
        end = date.today()
        start = end - timedelta(days=window_days)
        rows = await self._join_actuals(start=start, end=end, target_type=target_type)
        if not rows:
            return []

        by_key: dict[tuple[str, int], list[dict]] = {}
        for r in rows:
            key = (r["model_version"] or "unknown", int(r["horizon"]))
            by_key.setdefault(key, []).append(r)

        out: list[dict] = []
        for (version, horizon), pairs in by_key.items():
            metrics = _aggregate(pairs)
            out.append({
                "model_version": version,
                "horizon": horizon,
                "target_type": target_type,
                "n": metrics["n"],
                "mae": metrics["mae"],
                "mape": metrics["mape"],
                "coverage_p10_p90": metrics["coverage"],
            })
        out.sort(key=lambda x: (x["model_version"], x["horizon"]))
        return out

    # ── Internals ─────────────────────────────────────────────

    async def _join_actuals(
        self, *, start: date, end: date, target_type: str,
    ) -> list[dict]:
        sql = """
            SELECT
              af.id AS forecast_id,
              af.model_version,
              af.horizon,
              af.tanggal AS target_date,
              af.yhat::float AS yhat,
              af.p10::float AS p10,
              af.p90::float AS p90,
              fp.harga::float AS actual,
              af.commodity_id,
              af.region_id
            FROM analytics_forecast af
            JOIN fact_price_daily fp
              ON fp.commodity_id = af.commodity_id
             AND fp.region_id = af.region_id
             AND fp.tanggal = af.tanggal
            WHERE af.tanggal BETWEEN :start AND :end
              AND COALESCE(af.target_type, 'price') = :target_type
        """
        result = await self.db.execute(
            text(sql),
            {"start": start, "end": end, "target_type": target_type},
        )
        return [dict(r._mapping) for r in result]

    async def _persist_backtest(
        self,
        m: HorizonMetrics,
        start: date,
        end: date,
        now_naive: datetime,
    ) -> None:
        await self.db.execute(
            text("""
                INSERT INTO forecast_backtest_results
                  (model_name, model_type, target_type, horizon,
                   test_start_date, test_end_date,
                   mae, mape, coverage_p10_p90, metadata, created_at)
                VALUES
                  (:model_name, :model_type, :target_type, :horizon,
                   :start, :end,
                   :mae, :mape, :coverage, :metadata, :created)
            """),
            {
                "model_name": m.model_version,
                "model_type": _derive_type(m.model_version),
                "target_type": m.target_type,
                "horizon": m.horizon,
                "start": start,
                "end": end,
                "mae": _dec(m.mae),
                "mape": _dec(m.mape),
                "coverage": _dec(m.coverage_p10_p90),
                "metadata": _json({"n": m.n, "drift_flag": m.drift_flag}),
                "created": now_naive,
            },
        )


# ── Helpers ──────────────────────────────────────────────────

def _aggregate(pairs: list[dict]) -> dict[str, Any]:
    errs: list[float] = []
    pcts: list[float] = []
    cov_hits = 0
    for p in pairs:
        actual = float(p["actual"])
        yhat = float(p["yhat"])
        errs.append(abs(yhat - actual))
        if actual:
            pcts.append(abs(yhat - actual) / abs(actual) * 100)
        p10 = p.get("p10")
        p90 = p.get("p90")
        if p10 is not None and p90 is not None:
            if p10 <= actual <= p90:
                cov_hits += 1
    n = len(pairs)
    return {
        "n": n,
        "mae": round(statistics.fmean(errs), 4) if errs else 0.0,
        "mape": round(statistics.fmean(pcts), 4) if pcts else 0.0,
        "coverage": round(cov_hits / n, 4) if n else 0.0,
    }


def _drift_flag(recent: list[dict], baseline: list[dict]) -> bool:
    if not recent or not baseline:
        return False
    rec_pcts = [
        abs(float(p["yhat"]) - float(p["actual"])) / abs(float(p["actual"])) * 100
        for p in recent if float(p["actual"]) != 0
    ]
    base_pcts = [
        abs(float(p["yhat"]) - float(p["actual"])) / abs(float(p["actual"])) * 100
        for p in baseline if float(p["actual"]) != 0
    ]
    if not rec_pcts or not base_pcts:
        return False
    rec_avg = statistics.fmean(rec_pcts)
    base_avg = statistics.fmean(base_pcts)
    if base_avg <= 0 or math.isnan(rec_avg) or math.isnan(base_avg):
        return False
    return (rec_avg / base_avg) >= _DRIFT_RATIO_THRESHOLD


def _dec(v: float | None) -> Decimal | None:
    if v is None:
        return None
    return Decimal(str(v))


def _json(obj: dict) -> dict:
    """Return as-is so the JSONB column receives a native dict. SQLAlchemy
    handles the encoding."""
    return obj


def _derive_type(version: str) -> str:
    """Pull a coarse `model_type` from the version string. Best-effort —
    `forecast_backtest_results.model_type` is informational only."""
    v = (version or "").lower()
    for hint in ("lightgbm", "prophet", "sarimax", "tft", "stacking", "ensemble", "fallback"):
        if hint in v:
            return hint
    return "unknown"
