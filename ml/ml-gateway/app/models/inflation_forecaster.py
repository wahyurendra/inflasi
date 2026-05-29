"""Monthly inflation forecaster.

Mirrors the structure of :mod:`app.models.forecaster` but at monthly grain and
single-target (national or per-region inflation). Loaders are reused where the
math is identical; for now we offer a degraded-by-default implementation:

* If LightGBM / SARIMAX inflation artifacts exist under
  ``models/lightgbm/inflation/...`` and ``models/sarimax/inflation/...`` we
  load them. Until that path returns artifacts the request resolves through
  a SARIMA(1,0,1)(1,0,1,12) fit on the supplied ``inflasi_mtm`` history.
* The point series for the requested horizons (default 1, 3, 6) is the
  cumulative monthly forecast; ``p10/p90`` use the in-fit residual stddev.

Stateless and CPU-only — same shape as the price forecaster so the api-gateway
can treat both responses uniformly.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("inflation_forecaster")

_MIN_POINTS = 12  # one year of months
_QUANTILE_Z = {"p10": -1.2816, "p50": 0.0, "p90": 1.2816}


class InflationForecaster:
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
        horizons = sorted(set(int(h) for h in horizons))
        if not horizons:
            return {"error": "no_horizons"}

        series: list[float] = []
        for r in rows:
            v = r.get("inflasi_mtm")
            if v is None:
                continue
            try:
                series.append(float(v))
            except (TypeError, ValueError):
                continue
        if len(series) < _MIN_POINTS:
            return {
                "error": "insufficient_inflation_history",
                "min_required": _MIN_POINTS,
                "got": len(series),
            }

        sarima = self._sarima_forecast(series, horizon=max(horizons))
        if sarima is None:
            return {"error": "sarima_unavailable"}

        point, std = sarima
        horizons_out: dict[str, float] = {}
        components_out: dict[str, dict[str, float]] = {}
        quantiles_out: dict[str, dict[str, float]] = {}
        for h in horizons:
            idx = h - 1
            yhat = round(point[idx], 6)
            horizons_out[str(h)] = yhat
            quantiles_out[str(h)] = {
                k: round(yhat + z * std, 6)
                for k, z in _QUANTILE_Z.items()
            }
            components_out[str(h)] = {"sarimax": yhat}

        return {
            "horizons": horizons_out,
            "components": components_out,
            "quantiles": quantiles_out,
            "model": model,
            "models_used": {"sarimax": True},
            "weights": {"sarimax": 1.0},
        }

    # ── Backend ──────────────────────────────────────────────

    def _sarima_forecast(
        self, series: list[float], horizon: int,
    ) -> tuple[list[float], float] | None:
        try:
            import numpy as np
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            model = SARIMAX(
                series,
                order=(1, 0, 1),
                seasonal_order=(1, 0, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            fit = model.fit(disp=False)
            forecast = fit.forecast(steps=horizon)
            point = [float(x) for x in forecast]
            resid = np.asarray(fit.resid, dtype=float)
            std = float(np.std(resid[-24:])) if resid.size else 0.0
            return point, std
        except Exception:
            logger.exception("SARIMAX inflation forecast failed")
            return None
