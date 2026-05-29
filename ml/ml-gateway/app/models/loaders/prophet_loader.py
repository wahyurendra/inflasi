"""Prophet loader — per-series joblib artifacts.

Training (`ml/training/train_prophet.py`) fits one Prophet per top-N
``series_key_code``. Artifacts live under
``{base_dir}/series_{series_key_code}.joblib`` where ``base_dir`` is the active
``model_registry.artifact_path`` for ``model_type='prophet'`` (no horizon — the
model itself can be queried for any future date).

Returns ``None`` when no Prophet was trained for the requested series (small
tails) so the ensemble degrades gracefully.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.core.storage import get_store
from app.models.registry_client import get_registry_client

logger = logging.getLogger("loader.prophet")

# Same regressors the training script uses.
_REGRESSORS = (
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window", "school_holiday_flag",
    "harvest_flag", "rainfall_1d", "temperature_avg", "rainfall_anomaly",
    "extreme_weather_flag", "inflation_mom_lag_1", "inflation_yoy_lag_1",
    "usd_idr_change", "bi_rate", "fuel_price_flag",
)


class ProphetLoader:
    """Returns ``{"yhat", "p10", "p90", "version"}`` or ``None``."""

    def predict(
        self,
        history_df: pd.DataFrame,
        series_key: int,
        horizon: int,
    ) -> dict[str, Any] | None:
        ref = get_registry_client().get_active(
            model_type="prophet", target_type="price", horizon=None,
        )
        if ref is None:
            return None

        key = f"{ref.artifact_path.rstrip('/')}/series_{series_key}.joblib"
        model = get_store().load_joblib(key)
        if model is None:
            return None  # No artifact for this series — skip silently.

        active_regressors: list[str] = []
        for c in _REGRESSORS:
            if c in history_df.columns:
                col = history_df[c]
                if isinstance(col, pd.Series) and bool(col.notna().any()):
                    active_regressors.append(c)

        try:
            future = _build_future_frame(history_df, horizon, active_regressors)
            fc = model.predict(future).tail(horizon)
            return {
                "yhat": fc["yhat"].astype(float).tolist(),
                "p10": fc["yhat_lower"].astype(float).tolist(),
                "p90": fc["yhat_upper"].astype(float).tolist(),
                "version": ref.version,
            }
        except Exception:
            logger.exception("Prophet predict failed for series %s", series_key)
            return None


def _build_future_frame(
    history_df: pd.DataFrame, horizon: int, regressors: list[str],
) -> pd.DataFrame:
    """Build the Prophet ``future`` frame including last-known regressor values."""
    hist = history_df.sort_values("date").copy()
    hist["ds"] = pd.to_datetime(hist["date"])
    last_ds = hist["ds"].iloc[-1]
    future_dates = pd.date_range(
        start=last_ds + pd.Timedelta(days=1), periods=horizon, freq="D",
    )
    future = pd.DataFrame({"ds": list(hist["ds"]) + list(future_dates)})
    if regressors:
        # Carry last-known regressor values forward into the prediction window.
        for c in regressors:
            series = pd.to_numeric(hist[c], errors="coerce")
            assert isinstance(series, pd.Series)
            filled = series.fillna(0.0)
            last_val = float(filled.iloc[-1]) if len(filled) else 0.0
            forward = [last_val] * horizon
            future[c] = list(filled.values) + forward
    return future
