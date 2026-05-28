"""Ensemble price forecaster: ARIMA + Prophet (CPU) + optional TFT (GPU).

Two entry points:
- `predict(series, horizon)` — univariate, kept for backwards compatibility.
- `predict_features(rows, horizons)` — multivariate; consumes a list of
  `unified_ready_dataset` feature rows and returns predictions for each
  requested horizon. Prophet gains weather/macro/holiday regressors.

Stateless. Heavy libs are imported lazily so missing/failed models are skipped
and the ensemble re-normalises over whatever succeeded.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("forecaster")

_WEIGHTS = {"arima": 0.3, "prophet": 0.3, "tft": 0.4}
_MIN_POINTS = 30

# Columns passed to Prophet as additional regressors (when present & populated).
_REGRESSORS = (
    "rainfall_1d",
    "temperature_avg",
    "rainfall_anomaly",
    "extreme_weather_flag",
    "usd_idr_change",
    "bi_rate",
    "fuel_price_flag",
    "ramadan_flag",
    "lebaran_minus_7",
    "lebaran_plus_7",
    "idul_adha_window",
    "harvest_flag",
)


class EnsembleForecaster:
    # ── Univariate (legacy) ───────────────────────────────────

    def predict(self, series: list[float], horizon_days: int = 30) -> dict:
        if len(series) < _MIN_POINTS:
            return {"error": "insufficient_data", "min_required": _MIN_POINTS, "got": len(series)}

        results = {
            "arima": self._arima(series, horizon_days),
            "prophet": self._prophet_univariate(series, horizon_days),
            "tft": self._tft(series, horizon_days),
        }
        return {
            "horizon_days": horizon_days,
            "ensemble": self._ensemble(results, horizon_days),
            "models_used": {k: v is not None for k, v in results.items()},
        }

    # ── Multivariate (feature_store_daily) ────────────────────

    def predict_features(
        self,
        rows: list[dict[str, Any]],
        horizons: list[int],
        model: str = "ensemble",
    ) -> dict:
        if len(rows) < _MIN_POINTS:
            return {
                "error": "insufficient_data",
                "min_required": _MIN_POINTS,
                "got": len(rows),
            }

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

        max_horizon = max(horizons)
        price_series = df["price"].astype(float).tolist()

        runs: dict[str, list[float] | None]
        if model == "arima":
            runs = {"arima": self._arima(price_series, max_horizon)}
        elif model == "prophet":
            runs = {"prophet": self._prophet_multivariate(df, max_horizon)}
        elif model == "tft":
            runs = {"tft": self._tft(price_series, max_horizon)}
        else:
            runs = {
                "arima": self._arima(price_series, max_horizon),
                "prophet": self._prophet_multivariate(df, max_horizon),
                "tft": self._tft(price_series, max_horizon),
            }

        ensemble = self._ensemble(runs, max_horizon)
        horizons_out: dict[str, list[float]] = {}
        for h in horizons:
            horizons_out[str(h)] = ensemble[:h] if ensemble else []
        return {
            "horizons": horizons_out,
            "model": model,
            "models_used": {k: v is not None for k, v in runs.items()},
        }

    # ── Backends ──────────────────────────────────────────────

    def _arima(self, series: list[float], horizon: int) -> list[float] | None:
        try:
            from statsmodels.tsa.arima.model import ARIMA

            fit = ARIMA(series, order=(2, 1, 2)).fit()
            return [round(float(x), 2) for x in fit.forecast(steps=horizon)]
        except Exception:
            logger.exception("ARIMA failed")
            return None

    def _prophet_univariate(self, series: list[float], horizon: int) -> list[float] | None:
        try:
            import pandas as pd
            from prophet import Prophet

            df = pd.DataFrame({
                "ds": pd.date_range(end=pd.Timestamp.today(), periods=len(series)),
                "y": series,
            })
            m = Prophet(weekly_seasonality=True, yearly_seasonality=True)
            m.fit(df)
            fc = m.predict(m.make_future_dataframe(periods=horizon)).tail(horizon)
            return [round(float(x), 2) for x in fc["yhat"].tolist()]
        except Exception:
            logger.exception("Prophet (univariate) failed")
            return None

    def _prophet_multivariate(self, df, horizon: int) -> list[float] | None:
        try:
            import pandas as pd
            from prophet import Prophet

            # Identify regressors that are actually populated.
            active_regressors = [
                col for col in _REGRESSORS
                if col in df.columns and df[col].notna().any()
            ]

            train = pd.DataFrame({
                "ds": pd.to_datetime(df["date"]),
                "y": df["price"].astype(float),
            })
            for col in active_regressors:
                train[col] = df[col].astype(float).fillna(0.0).values

            m = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
                interval_width=0.80,
            )
            for col in active_regressors:
                m.add_regressor(col)
            m.fit(train)

            future = m.make_future_dataframe(periods=horizon, freq="D")
            # Carry last-known regressor values forward into the horizon window.
            if active_regressors:
                last_known = {c: float(train[c].iloc[-1]) for c in active_regressors}
                for col in active_regressors:
                    series = train.set_index("ds")[col]
                    future[col] = future["ds"].map(series).fillna(last_known[col])

            fc = m.predict(future).tail(horizon)
            return [round(float(x), 2) for x in fc["yhat"].tolist()]
        except Exception:
            logger.exception("Prophet (multivariate) failed")
            return None

    def _tft(self, series: list[float], horizon: int) -> list[float] | None:
        # GPU TFT path — needs torch + trained checkpoint (shipped by training
        # pipeline, not yet present). Returns None until then so the ensemble
        # degrades gracefully.
        try:
            import torch  # noqa: F401
        except Exception:
            return None
        return None

    @staticmethod
    def _ensemble(results: dict, horizon: int) -> list[float]:
        active = {k: v for k, v in results.items() if v}
        if not active:
            return []
        total_w = sum(_WEIGHTS.get(k, 1.0) for k in active)
        out = [0.0] * horizon
        for name, values in active.items():
            w = _WEIGHTS.get(name, 1.0) / total_w
            for i in range(min(horizon, len(values))):
                out[i] += values[i] * w
        return [round(v, 2) for v in out]
