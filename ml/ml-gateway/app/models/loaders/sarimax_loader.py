"""SARIMAX loader — per-series statsmodels artifacts.

Training (`ml/training/train_sarimax.py`) fits SARIMAX with order (1,1,1) and
seasonal (1,0,1,7) for the top-N ``series_key_code`` series. The artifact at
``{base}/series_{series_key_code}.joblib`` is the fit object returned by
``SARIMAX(...).fit()`` — supports ``.forecast(steps, exog=...)``.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.core.storage import get_store
from app.models.registry_client import get_registry_client

logger = logging.getLogger("loader.sarimax")

_EXOG = (
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window", "school_holiday_flag",
    "harvest_flag", "rainfall_1d", "temperature_avg", "rainfall_anomaly",
    "extreme_weather_flag", "inflation_mom_lag_1", "inflation_yoy_lag_1",
    "usd_idr_change", "bi_rate", "fuel_price_flag",
)


class SARIMAXLoader:
    """Returns ``{"yhat": list[float], "version": str}`` or ``None``."""

    def predict(
        self,
        history_df: pd.DataFrame,
        series_key: int,
        horizon: int,
    ) -> dict[str, Any] | None:
        ref = get_registry_client().get_active(
            model_type="sarimax", target_type="price", horizon=None,
        )
        if ref is None:
            return None

        key = f"{ref.artifact_path.rstrip('/')}/series_{series_key}.joblib"
        fit = get_store().load_joblib(key)
        if fit is None:
            return None

        try:
            exog_cols = [c for c in _EXOG if c in history_df.columns]
            future_exog = _carry_forward_exog(history_df, horizon, exog_cols)
            forecast = fit.forecast(steps=horizon, exog=future_exog)
            values = [float(v) for v in forecast]
            return {"yhat": values, "version": ref.version}
        except Exception:
            logger.exception("SARIMAX predict failed for series %s", series_key)
            return None


def _carry_forward_exog(
    history_df: pd.DataFrame, horizon: int, exog_cols: list[str],
) -> pd.DataFrame | None:
    if not exog_cols:
        return None
    last_row = history_df[exog_cols].iloc[-1]
    out = pd.DataFrame([last_row] * horizon, columns=exog_cols).reset_index(drop=True)
    for c in exog_cols:
        col = pd.to_numeric(out[c], errors="coerce")
        assert isinstance(col, pd.Series)
        out[c] = col.fillna(0.0)
    return out
