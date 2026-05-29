"""TFT loader — PyTorch Lightning checkpoint with QuantileLoss [0.1, 0.5, 0.9].

Heavy deps (``torch``, ``pytorch_forecasting``, ``lightning``) live in the GPU
image only. Gated on ``import torch`` so the CPU image returns ``None`` and the
ensemble degrades to the other base models without erroring.

Training (`ml/training/train_tft.py`) saves the best checkpoint as a single
``.ckpt`` referenced by ``model_registry.artifact_path``. Inference re-builds a
``TimeSeriesDataSet`` from the supplied feature window using the same column
groupings the trainer used (KNOWN_REALS / OBSERVED_REALS / STATIC_CATEGORICALS).
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.core.storage import get_store
from app.models.registry_client import get_registry_client

logger = logging.getLogger("loader.tft")


_KNOWN_REALS = (
    "day_of_week", "week_of_year", "month", "quarter", "is_weekend",
    "is_month_start", "is_month_end",
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window", "school_holiday_flag",
    "harvest_flag",
)
_OBSERVED_REALS = (
    "price", "valid_price_flag", "is_imputed", "missing_gap_length",
    "anomaly_candidate", "data_quality_score", "missing_rate", "source_count",
    "price_lag_1", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_30", "rolling_std_7",
    "rolling_min_7", "rolling_max_7", "rolling_median_7", "rolling_median_30",
    "price_change_1d", "price_change_7d", "price_change_30d",
    "pct_change_1d", "pct_change_7d", "pct_change_30d",
    "missing_rate_30d", "is_imputed_count_30d",
    "rainfall_1d", "temperature_avg", "weather_station_count",
    "rainfall_anomaly", "extreme_weather_flag",
    "inflation_mom_lag_1", "inflation_yoy_lag_1", "usd_idr_change",
    "bi_rate", "fuel_price_flag", "has_weather", "has_macro",
    "has_complete_weather", "has_complete_macro",
)
_STATIC_CATEGORICALS = ("commodity_id", "region_id", "entity_id")


class TFTLoader:
    """Returns ``{"p10","p50","p90","version"}`` or ``None``."""

    def predict(
        self,
        features_df: pd.DataFrame,
        horizon: int,
    ) -> dict[str, Any] | None:
        try:
            import torch  # noqa: F401
        except Exception:
            return None  # CPU image — silently skip.
        try:
            from pytorch_forecasting import (  # type: ignore
                TemporalFusionTransformer,
                TimeSeriesDataSet,
            )
        except Exception:
            logger.debug("pytorch_forecasting unavailable; skipping TFT")
            return None

        ref = get_registry_client().get_active(
            model_type="tft", target_type="price", horizon=horizon,
        )
        if ref is None:
            return None

        ckpt_path = get_store().get_checkpoint_path(ref.artifact_path)
        if ckpt_path is None:
            return None

        try:
            model = TemporalFusionTransformer.load_from_checkpoint(ckpt_path)
        except Exception:
            logger.exception("TFT checkpoint load failed")
            return None

        try:
            frame = _prepare_frame(features_df)
            dataset = TimeSeriesDataSet.from_parameters(
                model.dataset_parameters, frame, predict=True,
            )
            loader = dataset.to_dataloader(train=False, batch_size=1)
            raw = model.predict(loader, mode="raw", return_x=False)
            quantiles = _extract_quantiles(raw, horizon)
            return {**quantiles, "version": ref.version}
        except Exception:
            logger.exception("TFT predict failed")
            return None


def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Match the trainer's prepare_tft_frame: sort, time_idx, series, fillna."""
    out = df.copy()
    out = out.sort_values(["series_key_code", "date"]) if "series_key_code" in out.columns else out.sort_values("date")
    out["date"] = pd.to_datetime(out["date"])
    out["time_idx"] = (out["date"] - out["date"].min()).dt.days.astype(int)
    series_col = "series_key_code" if "series_key_code" in out.columns else "series"
    out["series"] = out[series_col].astype(str)
    for c in _STATIC_CATEGORICALS:
        if c in out.columns:
            out[c] = out[c].astype(str)
    numeric_cols = [c for c in _KNOWN_REALS + _OBSERVED_REALS if c in out.columns]
    for c in numeric_cols + (["target"] if "target" in out.columns else []):
        col = pd.to_numeric(out[c], errors="coerce")
        assert isinstance(col, pd.Series)
        out[c] = col.replace([float("inf"), float("-inf")], None)
        out[c] = out.groupby("series")[c].transform(lambda s: s.ffill().bfill()).fillna(0)
    return out


def _extract_quantiles(raw: Any, horizon: int) -> dict[str, list[float]]:
    """Pull p10/p50/p90 from a TFT raw prediction.

    Raw shape is ``[batch, time, n_quantiles]`` when the loss is QuantileLoss
    over [0.1, 0.5, 0.9]. We take the first (and only) batch entry and slice
    out the three quantile series.
    """
    pred = raw["prediction"] if isinstance(raw, dict) else raw
    try:
        arr = pred.detach().cpu().numpy()
    except Exception:
        import numpy as np
        arr = np.asarray(pred)
    # arr shape: (1, T, 3)
    series = arr[0]
    n = min(horizon, series.shape[0])
    return {
        "p10": [float(v) for v in series[:n, 0]],
        "p50": [float(v) for v in series[:n, 1]],
        "p90": [float(v) for v in series[:n, 2]],
    }
