"""Ensemble price forecaster — loads trained artifacts from MinIO.

Five base models, all loaded lazily by the matching loader in
:mod:`app.models.loaders`:

* **LightGBM** — global model, native p10/p50/p90 quantile regression.
* **Prophet** — per-series, yhat + yhat_lower/upper (80% interval).
* **SARIMAX** — per-series, point only.
* **TFT** — global panel, native quantile via PyTorch Lightning (GPU image).
* **Stacking** — RidgeCV meta over the four base predictions.

When all artifacts are present the response carries real quantiles and a true
stacked point. When any loader returns ``None`` (missing artifact, MinIO down,
torch not installed) the ensemble degrades to a renormalized weighted average
over whatever survived. When *no* trained model loads at all we fall back to
the in-process ARIMA trained at request time, preserving the API's promise
that ``/forecast/predict`` never hard-errors on data alone.

Two entry points kept for backwards compatibility:

* :meth:`predict` — univariate (legacy, used by ``/forecast/prices``).
* :meth:`predict_features` — multivariate (used by ``/forecast/predict``).
"""

from __future__ import annotations

import logging
from typing import Any

from app.models.loaders.lightgbm_loader import LightGBMLoader
from app.models.loaders.prophet_loader import ProphetLoader
from app.models.loaders.sarimax_loader import SARIMAXLoader
from app.models.loaders.stacking_loader import StackingLoader
from app.models.loaders.tft_loader import TFTLoader

logger = logging.getLogger("forecaster")

_MIN_POINTS = 30
_DEFAULT_WEIGHTS = {"lightgbm": 0.35, "prophet": 0.25, "sarimax": 0.15, "tft": 0.25}


class EnsembleForecaster:
    def __init__(self) -> None:
        self._lgbm = LightGBMLoader()
        self._prophet = ProphetLoader()
        self._sarimax = SARIMAXLoader()
        self._tft = TFTLoader()
        self._stacking = StackingLoader()

    # ── Univariate (legacy) ───────────────────────────────────

    def predict(self, series: list[float], horizon_days: int = 30) -> dict:
        if len(series) < _MIN_POINTS:
            return {"error": "insufficient_data", "min_required": _MIN_POINTS, "got": len(series)}
        ar = self._train_arima_fallback(series, horizon_days)
        return {
            "horizon_days": horizon_days,
            "ensemble": ar or [],
            "models_used": {"arima_fallback": ar is not None},
        }

    # ── Multivariate (feature_store_daily) ────────────────────

    def predict_features(
        self,
        rows: list[dict[str, Any]],
        horizons: list[int],
        model: str = "ensemble",  # kept for API stability; ignored when artifacts exist
    ) -> dict:
        if len(rows) < _MIN_POINTS:
            return {"error": "insufficient_data", "min_required": _MIN_POINTS, "got": len(rows)}

        try:
            import pandas as pd
        except Exception:
            logger.exception("pandas unavailable")
            return {"error": "pandas_unavailable"}

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df = df.dropna(subset=["price"])
        if len(df) < _MIN_POINTS:
            return {"error": "insufficient_data", "min_required": _MIN_POINTS, "got": len(df)}

        last_row = df.iloc[-1]
        series_key = int(last_row.get("series_key_code") or 0)
        last_month = int(last_row.get("month") or pd.Timestamp(last_row["date"]).month)
        last_dow = int(last_row.get("day_of_week") or pd.Timestamp(last_row["date"]).dayofweek)

        horizons_out: dict[str, list[float]] = {}
        components_out: dict[str, dict[str, list[float]]] = {}
        quantiles_out: dict[str, dict[str, list[float]]] = {}
        per_horizon_used: dict[int, dict[str, bool]] = {}
        per_horizon_versions: dict[int, dict[str, str]] = {}

        for h in horizons:
            lgb = self._lgbm.predict(df, h)
            pr = self._prophet.predict(df, series_key, h)
            sa = self._sarimax.predict(df, series_key, h)
            tft = self._tft.predict(df, h)

            used = {
                "lightgbm": lgb is not None,
                "prophet": pr is not None,
                "sarimax": sa is not None,
                "tft": tft is not None,
            }
            versions: dict[str, str] = {}
            if lgb:
                versions["lightgbm"] = lgb["version"]
            if pr:
                versions["prophet"] = pr["version"]
            if sa:
                versions["sarimax"] = sa["version"]
            if tft:
                versions["tft"] = tft["version"]

            # Per-step point predictions for each base model, padded to length h.
            comp: dict[str, list[float]] = {}
            if lgb:
                comp["lightgbm"] = list(lgb["point"][:h])
            if pr:
                comp["prophet"] = list(pr["yhat"][:h])
            if sa:
                comp["sarimax"] = list(sa["yhat"][:h])
            if tft:
                comp["tft"] = list(tft["p50"][:h])

            if not comp:
                # Last-resort fallback so the API doesn't 500: in-process ARIMA.
                ar = self._train_arima_fallback([float(p) for p in df["price"].tolist()], h)
                if ar:
                    comp["arima_fallback"] = ar
                    used["arima_fallback"] = True
                    versions["arima_fallback"] = "in-process"

            point = self._stack_or_weighted_average(
                comp, series_key=series_key, month=last_month, day_of_week=last_dow,
            )
            qbands = self._compose_quantiles(lgb, pr, tft, point)

            horizons_out[str(h)] = point
            components_out[str(h)] = comp
            quantiles_out[str(h)] = qbands
            per_horizon_used[h] = used
            per_horizon_versions[h] = versions

        # Flatten to the legacy contract the api-gateway already reads.
        flat_used = self._merge_used(per_horizon_used)
        flat_versions = self._merge_versions(per_horizon_versions)
        weights = _renormalize({k: _DEFAULT_WEIGHTS[k] for k in flat_used if k in _DEFAULT_WEIGHTS and flat_used[k]})

        return {
            "horizons": horizons_out,
            "components": components_out,
            "quantiles": quantiles_out,
            "model": model,
            "models_used": flat_used,
            "weights": weights,
            "model_versions": flat_versions,
        }

    # ── Stacking / weighting ──────────────────────────────────

    def _stack_or_weighted_average(
        self,
        components: dict[str, list[float]],
        *,
        series_key: int,
        month: int,
        day_of_week: int,
    ) -> list[float]:
        """For each step: prefer the trained stacker, else renormalized weighted avg."""
        if not components:
            return []
        steps = max(len(v) for v in components.values())
        out: list[float] = []
        for i in range(steps):
            base_preds = {
                name: (values[i] if i < len(values) else None)
                for name, values in components.items()
            }
            stack = self._stacking.predict(
                base_preds=base_preds,
                month=month,
                day_of_week=day_of_week,
                series_key_code=series_key,
            )
            if stack is not None:
                out.append(round(stack["yhat"], 2))
                continue
            # Renormalized weighted average over present base models.
            weights = _renormalize({
                name: _DEFAULT_WEIGHTS.get(name, 0.0)
                for name, v in base_preds.items() if v is not None
            })
            avg = sum((base_preds[name] or 0.0) * w for name, w in weights.items())
            out.append(round(avg, 2))
        return out

    def _compose_quantiles(
        self,
        lgb: dict[str, Any] | None,
        pr: dict[str, Any] | None,
        tft: dict[str, Any] | None,
        point: list[float],
    ) -> dict[str, list[float]]:
        """Prefer LightGBM's native quantiles. Fall back to TFT, then Prophet bands,
        then the point series as p50 with zero-width bands."""
        if lgb:
            return {
                "p10": list(lgb["p10"][:len(point)]),
                "p50": list(lgb["p50"][:len(point)]),
                "p90": list(lgb["p90"][:len(point)]),
            }
        if tft:
            return {
                "p10": list(tft["p10"][:len(point)]),
                "p50": list(tft["p50"][:len(point)]),
                "p90": list(tft["p90"][:len(point)]),
            }
        if pr:
            return {
                "p10": list(pr["p10"][:len(point)]),
                "p50": list(pr["yhat"][:len(point)]),
                "p90": list(pr["p90"][:len(point)]),
            }
        return {"p10": list(point), "p50": list(point), "p90": list(point)}

    # ── ARIMA fallback (legacy + safety net) ──────────────────

    def _train_arima_fallback(self, series: list[float], horizon: int) -> list[float] | None:
        try:
            from statsmodels.tsa.arima.model import ARIMA

            fit = ARIMA(series, order=(2, 1, 2)).fit()
            return [round(float(x), 2) for x in fit.forecast(steps=horizon)]
        except Exception:
            logger.exception("ARIMA fallback failed")
            return None

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _merge_used(per_horizon: dict[int, dict[str, bool]]) -> dict[str, bool]:
        merged: dict[str, bool] = {}
        for d in per_horizon.values():
            for k, v in d.items():
                merged[k] = merged.get(k, False) or v
        return merged

    @staticmethod
    def _merge_versions(per_horizon: dict[int, dict[str, str]]) -> dict[str, str]:
        merged: dict[str, str] = {}
        for d in per_horizon.values():
            for k, v in d.items():
                merged.setdefault(k, v)
        return merged


def _renormalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if not total:
        return {}
    return {k: round(v / total, 4) for k, v in weights.items()}
