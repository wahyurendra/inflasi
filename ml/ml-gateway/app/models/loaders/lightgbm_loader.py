"""LightGBM loader — point + p10/p50/p90 quantile models per horizon.

Training (`ml/training/train_lightgbm.py`) produces four joblibs per horizon:
``point.joblib`` and ``quantile_p{10,50,90}.joblib``. Each is a dict
``{"model": LGBMRegressor, "features": list[str]}`` (or with an extra
``"alpha"`` for quantiles). Registered in ``model_registry`` with
``artifact_path`` pointing at the **directory** holding the four files.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.core.storage import get_store
from app.models.registry_client import get_registry_client

logger = logging.getLogger("loader.lightgbm")


class LightGBMLoader:
    """Returns ``{"point", "p10", "p50", "p90", "version"}`` or ``None``."""

    def predict(
        self,
        features_df: pd.DataFrame,
        horizon: int,
        *,
        n_steps: int | None = None,
    ) -> dict[str, Any] | None:
        ref = get_registry_client().get_active(
            model_type="lightgbm", target_type="price", horizon=horizon,
        )
        if ref is None:
            return None

        store = get_store()
        base = ref.artifact_path.rstrip("/")
        try:
            point = store.load_joblib(f"{base}/point.joblib")
            q10 = store.load_joblib(f"{base}/quantile_p10.joblib")
            q50 = store.load_joblib(f"{base}/quantile_p50.joblib")
            q90 = store.load_joblib(f"{base}/quantile_p90.joblib")
        except Exception:
            logger.exception("LightGBM artifact fetch failed (%s)", base)
            return None
        if not (point and q10 and q50 and q90):
            return None

        try:
            X = _build_matrix(features_df, point.get("features", []))
        except Exception:
            logger.exception("LightGBM feature matrix build failed")
            return None

        # The training notebook treats target as H+horizon — so a single matrix row
        # produces a single scalar prediction. We replicate the last-known row for
        # each step out to ``n_steps`` so downstream code can slice as needed.
        steps = n_steps or horizon
        last = X.iloc[-1:].copy()
        repeated = pd.concat([last] * steps, ignore_index=True)
        try:
            point_pred = point["model"].predict(repeated).astype(float).tolist()
            p10_pred = q10["model"].predict(repeated).astype(float).tolist()
            p50_pred = q50["model"].predict(repeated).astype(float).tolist()
            p90_pred = q90["model"].predict(repeated).astype(float).tolist()
        except Exception:
            logger.exception("LightGBM .predict failed")
            return None

        # Enforce monotonic quantiles per step (training does the same post-fit).
        for i in range(len(point_pred)):
            lo, mid, hi = sorted([p10_pred[i], p50_pred[i], p90_pred[i]])
            p10_pred[i], p50_pred[i], p90_pred[i] = lo, mid, hi

        return {
            "point": point_pred,
            "p10": p10_pred,
            "p50": p50_pred,
            "p90": p90_pred,
            "version": ref.version,
        }


def _build_matrix(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Restrict to the trained-on columns, median-fill NaNs (same as `clean_xy`)."""
    if not feature_cols:
        # Fallback: drop obvious non-features.
        drop = {"date", "split", "target", "row_role"}
        feature_cols = [c for c in df.columns if c not in drop]
    keep = [c for c in feature_cols if c in df.columns]
    X = df.loc[:, keep].copy()
    # Fill missing trained columns with 0 — better than KeyError when the live
    # schema drifts behind training. Logs a warning at the call site is fine.
    for c in feature_cols:
        if c not in X.columns:
            X[c] = 0
    # Reorder to match training.
    X = X.loc[:, feature_cols]
    X = X.replace([float("inf"), float("-inf")], None)
    med = X.median(numeric_only=True)
    X = X.fillna(med).fillna(0)
    return X
