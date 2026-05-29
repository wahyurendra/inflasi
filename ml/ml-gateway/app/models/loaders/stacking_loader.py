"""Stacking meta-model loader — RidgeCV over base predictions + meta features.

Training (`ml/training/train_ensemble.py`) fits a sklearn ``Pipeline([Scaler,
RidgeCV])`` whose feature columns are::

    pred_lgbm, pred_sarimax, pred_prophet, pred_tft,
    model_mean, model_std, model_min, model_max, model_range,
    month, day_of_week, series_key_code

The artifact joblib is a dict ``{"model", "features", "model_names"}`` so we
can verify column alignment and reorder gracefully when a base model is absent
(missing pred → fill with the mean of present predictions, same as the
notebook's fillna(0) after meta feature derivation).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.core.storage import get_store
from app.models.registry_client import get_registry_client

logger = logging.getLogger("loader.stacking")


class StackingLoader:
    """Returns ``{"yhat": float, "version": str}`` per step, or ``None``."""

    def predict(
        self,
        *,
        base_preds: dict[str, float | None],
        month: int,
        day_of_week: int,
        series_key_code: int,
    ) -> dict[str, Any] | None:
        ref = get_registry_client().get_active(
            model_type="stacking", target_type="price", horizon=None,
        )
        if ref is None:
            return None

        artifact = get_store().load_joblib(ref.artifact_path)
        if artifact is None or "model" not in artifact:
            return None
        model = artifact["model"]
        feature_cols: list[str] = list(artifact.get("features") or [])

        row = _build_meta_row(
            base_preds=base_preds,
            month=month,
            day_of_week=day_of_week,
            series_key_code=series_key_code,
            feature_cols=feature_cols,
        )
        if row is None:
            return None
        try:
            yhat = float(model.predict(pd.DataFrame([row], columns=feature_cols))[0])
            return {"yhat": yhat, "version": ref.version}
        except Exception:
            logger.exception("stacking predict failed")
            return None


def _build_meta_row(
    *,
    base_preds: dict[str, float | None],
    month: int,
    day_of_week: int,
    series_key_code: int,
    feature_cols: list[str],
) -> dict[str, float] | None:
    """Assemble the meta feature row in the exact column order the model was trained on."""
    present = [v for v in base_preds.values() if v is not None]
    if not present:
        return None
    mean_present = float(np.mean(present))

    # Default base predictions to the mean of present ones (graceful when a model is missing).
    pred_cols = {f"pred_{k}": (float(v) if v is not None else mean_present) for k, v in base_preds.items()}

    # Recompute meta features from the (possibly imputed) predictions for consistency.
    vals = list(pred_cols.values())
    row: dict[str, float] = {
        **pred_cols,
        "model_mean": float(np.mean(vals)),
        "model_std": float(np.std(vals, ddof=0)),
        "model_min": float(np.min(vals)),
        "model_max": float(np.max(vals)),
        "model_range": float(np.max(vals) - np.min(vals)),
        "month": float(month),
        "day_of_week": float(day_of_week),
        "series_key_code": float(series_key_code),
    }
    # If the trained model expects extra columns we don't have, default to 0.
    for c in feature_cols:
        row.setdefault(c, 0.0)
    return row
