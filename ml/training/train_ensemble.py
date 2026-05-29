"""Train the RidgeCV stacking meta-model from base-model validation predictions.

Expects each base trainer to have written
``base_predictions/{model}/h{horizon}/valid_predictions.parquet`` (date,
series_key_code, target, prediction). This script merges them on
``(date, series_key_code)``, fits a Ridge on validation, and uploads the joblib.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.training.common import (
    TrainingConfig,
    artifact_dir,
    get_minio_client,
    register_model,
    save_metrics_local,
    setup_logging,
)

logger = logging.getLogger("training.ensemble")

_KEYS = ("date", "series_key_code")
_BASES = ("lgbm", "sarimax", "prophet", "tft")


def _read_pred(cfg: TrainingConfig, key: str, name: str) -> pd.DataFrame:
    """Download a base-model prediction parquet from MinIO and add prefix."""
    local = Path(cfg.local_cache) / "ensemble_inputs" / Path(key).name
    local.parent.mkdir(parents=True, exist_ok=True)
    if not local.exists():
        client = get_minio_client(cfg)
        client.fget_object(cfg.minio_datasets_bucket, key, str(local))
    df = pd.read_parquet(local)
    df["date"] = pd.to_datetime(df["date"])
    cols = list(_KEYS) + ["target", "prediction"]
    df = df.loc[:, [c for c in cols if c in df.columns]]
    return df.rename(columns={"prediction": f"pred_{name}"})


def _merge(frames: list[pd.DataFrame]) -> pd.DataFrame:
    base = frames[0]
    for nxt in frames[1:]:
        if "target" in nxt.columns:
            nxt = nxt.drop(columns=["target"])
        base = base.merge(nxt, on=list(_KEYS), how="inner")
    return base


def _add_meta(df: pd.DataFrame) -> pd.DataFrame:
    pred_cols = [c for c in df.columns if c.startswith("pred_")]
    out = df.copy()
    out["model_mean"] = out[pred_cols].mean(axis=1)
    std = out[pred_cols].std(axis=1)
    assert isinstance(std, pd.Series)
    out["model_std"] = std.fillna(0)
    out["model_min"] = out[pred_cols].min(axis=1)
    out["model_max"] = out[pred_cols].max(axis=1)
    out["model_range"] = out["model_max"] - out["model_min"]
    out["month"] = pd.to_datetime(out["date"]).dt.month
    out["day_of_week"] = pd.to_datetime(out["date"]).dt.dayofweek
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument(
        "--valid-files", nargs="+",
        default=[
            "base_predictions/lgbm/valid.parquet",
            "base_predictions/sarimax/valid.parquet",
            "base_predictions/prophet/valid.parquet",
            "base_predictions/tft/valid.parquet",
        ],
    )
    parser.add_argument("--names", nargs="+", default=list(_BASES))
    parser.add_argument("--no-register", action="store_true")
    args = parser.parse_args()

    setup_logging()
    cfg = TrainingConfig.from_env(horizon=args.horizon)

    if len(args.valid_files) != len(args.names):
        raise ValueError("--valid-files and --names must have the same length")

    frames = []
    for key, name in zip(args.valid_files, args.names):
        try:
            frames.append(_read_pred(cfg, key, name))
        except Exception as e:
            logger.warning("skip %s (%s): %s", name, key, e)
    if len(frames) < 2:
        logger.error("need at least 2 base models to stack; got %s", len(frames))
        return

    merged = _add_meta(_merge(frames))
    feature_cols = [c for c in merged.columns if c.startswith("pred_") or c in (
        "model_mean", "model_std", "model_min", "model_max", "model_range",
        "month", "day_of_week", "series_key_code",
    )]
    X = merged[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = merged["target"].astype(float)

    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    meta = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0])),
    ])
    meta.fit(X, y)

    cache = Path(cfg.local_cache) / "ensemble" / cfg.version
    cache.mkdir(parents=True, exist_ok=True)
    local = cache / "stacking_meta_model.joblib"
    joblib.dump({"model": meta, "features": feature_cols, "model_names": args.names}, local)

    base_dir = artifact_dir(cfg, model_type="stacking", horizon=None)
    remote_key = f"{base_dir}/stacking_meta_model.joblib"
    from ml.training.common import upload_file
    upload_file(cfg, local, remote_key)

    metrics = {
        "n_rows": int(len(merged)),
        "n_features": len(feature_cols),
        "ridge_alpha": float(meta.named_steps["model"].alpha_),
    }
    save_metrics_local(metrics, cache / "metrics.json")
    if not args.no_register:
        register_model(
            cfg,
            model_name="stacking-ridge",
            model_type="stacking",
            target_type="price",
            artifact_path=remote_key,
            horizon=None,
            metrics=metrics,
        )


if __name__ == "__main__":
    main()
