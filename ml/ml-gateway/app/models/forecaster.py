"""Ensemble price forecaster: ARIMA + Prophet (CPU) + optional TFT (GPU).

Stateless — the caller passes the historical daily price series; we return an
ensemble forecast. Heavy libs are imported lazily, so missing/failed models are
skipped and the ensemble re-normalises over whatever succeeded.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("forecaster")

_WEIGHTS = {"arima": 0.3, "prophet": 0.3, "tft": 0.4}
_MIN_POINTS = 30


class EnsembleForecaster:
    def predict(self, series: list[float], horizon_days: int = 30) -> dict:
        if len(series) < _MIN_POINTS:
            return {"error": "insufficient_data", "min_required": _MIN_POINTS, "got": len(series)}

        results = {
            "arima": self._arima(series, horizon_days),
            "prophet": self._prophet(series, horizon_days),
            "tft": self._tft(series, horizon_days),
        }
        return {
            "horizon_days": horizon_days,
            "ensemble": self._ensemble(results, horizon_days),
            "models_used": {k: v is not None for k, v in results.items()},
        }

    def _arima(self, series: list[float], horizon: int) -> "list[float] | None":
        try:
            from statsmodels.tsa.arima.model import ARIMA

            model = ARIMA(series, order=(2, 1, 2)).fit()
            return [round(float(x), 2) for x in model.forecast(steps=horizon)]
        except Exception:
            logger.exception("ARIMA failed")
            return None

    def _prophet(self, series: list[float], horizon: int) -> "list[float] | None":
        try:
            import pandas as pd
            from prophet import Prophet

            df = pd.DataFrame(
                {"ds": pd.date_range(end=pd.Timestamp.today(), periods=len(series)), "y": series}
            )
            m = Prophet(weekly_seasonality=True, yearly_seasonality=True)
            m.fit(df)
            fc = m.predict(m.make_future_dataframe(periods=horizon)).tail(horizon)
            return [round(float(x), 2) for x in fc["yhat"].tolist()]
        except Exception:
            logger.exception("Prophet failed")
            return None

    def _tft(self, series: list[float], horizon: int) -> "list[float] | None":
        # GPU TFT path — requires torch + a trained checkpoint (shipped by the training
        # pipeline, not yet present). Returns None until then so the ensemble degrades.
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
        total_w = sum(_WEIGHTS[k] for k in active)
        out = [0.0] * horizon
        for name, values in active.items():
            w = _WEIGHTS[name] / total_w
            for i in range(min(horizon, len(values))):
                out[i] += values[i] * w
        return [round(v, 2) for v in out]
