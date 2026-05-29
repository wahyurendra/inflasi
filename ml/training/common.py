"""Shared training utilities — dataset loading, metrics, MinIO upload, registry POST.

Mirrors the helper functions in the user's notebook so the training scripts read
like simplified versions of it. Each ``train_*.py`` reads a parquet from MinIO
(or the local cache), trains its model, writes the artifact(s) back to MinIO,
then POSTs to ``/api/v1/admin/models`` to register the new version. Promotion to
``is_active = true`` is a separate operator step (avoid auto-promote until
backtest confirms).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger("training.common")

# Columns that must never appear in the feature matrix — they're either the
# target itself, identifiers, or pre-encoded versions thereof. Mirrors the
# training notebook's LEAKAGE_COLUMNS set.
LEAKAGE_COLUMNS: frozenset[str] = frozenset({
    "target",
    "split",
    "date",
    "commodity_name",
    "region_name",
    "entity_name",
    "commodity_id",
    "region_id",
    "entity_id",
})

DEFAULT_FEATURES: tuple[str, ...] = (
    "price", "valid_price_flag", "is_imputed", "missing_gap_length", "anomaly_candidate",
    "data_quality_score", "missing_rate", "source_count", "day_of_week", "week_of_year",
    "month", "quarter", "is_weekend", "is_month_start", "is_month_end",
    "price_lag_1", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_30", "rolling_std_7",
    "rolling_min_7", "rolling_max_7", "rolling_median_7", "rolling_median_30",
    "price_change_1d", "price_change_7d", "price_change_30d", "pct_change_1d",
    "pct_change_7d", "pct_change_30d", "missing_rate_30d", "is_imputed_count_30d",
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window", "school_holiday_flag",
    "harvest_flag", "rainfall_1d", "temperature_avg", "weather_station_count",
    "rainfall_anomaly", "extreme_weather_flag", "inflation_mom_lag_1",
    "inflation_yoy_lag_1", "usd_idr_change", "bi_rate", "fuel_price_flag",
    "has_weather", "has_macro", "commodity_id_code", "region_id_code", "entity_id_code",
    "series_family_code", "frequency_code", "entity_level_code", "unit_code",
    "has_complete_weather", "has_complete_macro", "series_key_code",
)


# ── Config ────────────────────────────────────────────────────


@dataclass
class TrainingConfig:
    horizon: int = 7
    dataset_path: str = "datasets/train_ready_h7.parquet"  # MinIO key
    artifact_prefix: str = "models"                         # MinIO key prefix
    version: str = "v1"                                     # bump per training run
    api_gateway_url: str = "http://inflasi-api:8080"
    minio_endpoint: str = "inflasi-minio:9000"
    minio_bucket: str = "inflasi-models"
    minio_datasets_bucket: str = "inflasi-models"           # reuse same bucket
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_secure: bool = False
    local_cache: str = "/tmp/inflasi-training"

    @classmethod
    def from_env(cls, *, horizon: int = 7) -> "TrainingConfig":
        return cls(
            horizon=horizon,
            dataset_path=os.environ.get(
                "TRAIN_DATASET_PATH", f"datasets/train_ready_h{horizon}.parquet"
            ),
            artifact_prefix=os.environ.get("ARTIFACT_PREFIX", "models"),
            version=os.environ.get("MODEL_VERSION", "v1"),
            api_gateway_url=os.environ.get("API_GATEWAY_URL", "http://inflasi-api:8080"),
            minio_endpoint=os.environ.get("MINIO_ENDPOINT", "inflasi-minio:9000"),
            minio_bucket=os.environ.get("MINIO_BUCKET", "inflasi-models"),
            minio_datasets_bucket=os.environ.get("MINIO_DATASETS_BUCKET", "inflasi-models"),
            minio_access_key=os.environ.get("MINIO_ACCESS_KEY", ""),
            minio_secret_key=os.environ.get("MINIO_SECRET_KEY", ""),
            minio_secure=os.environ.get("MINIO_SECURE", "false").lower() in {"1", "true", "yes"},
            local_cache=os.environ.get("LOCAL_CACHE", "/tmp/inflasi-training"),
        )


# ── MinIO helpers ─────────────────────────────────────────────


def get_minio_client(cfg: TrainingConfig):
    """Return a configured MinIO client. Raises if creds missing."""
    from minio import Minio  # type: ignore

    if not cfg.minio_access_key or not cfg.minio_secret_key:
        raise RuntimeError("MINIO_ACCESS_KEY / MINIO_SECRET_KEY required")
    return Minio(
        cfg.minio_endpoint,
        access_key=cfg.minio_access_key,
        secret_key=cfg.minio_secret_key,
        secure=cfg.minio_secure,
    )


def download_parquet(cfg: TrainingConfig, key: str | None = None) -> Path:
    """Download a parquet from MinIO; return the local cached path."""
    key = key or cfg.dataset_path
    local = Path(cfg.local_cache) / key
    local.parent.mkdir(parents=True, exist_ok=True)
    if not local.exists():
        client = get_minio_client(cfg)
        client.fget_object(cfg.minio_datasets_bucket, key, str(local))
    return local


def upload_file(cfg: TrainingConfig, local_path: str | Path, key: str) -> str:
    """Upload a single file to ``cfg.minio_bucket/{key}``; return the key."""
    client = get_minio_client(cfg)
    client.fput_object(cfg.minio_bucket, key, str(local_path))
    return key


# ── Dataset helpers ───────────────────────────────────────────


def load_dataset(path: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    sort_key = ["series_key_code", "date"] if "series_key_code" in df.columns else ["date"]
    return df.sort_values(sort_key).reset_index(drop=True)


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["split"].eq("train")].copy()
    valid = df[df["split"].eq("validation")].copy()
    test = df[df["split"].eq("test")].copy()
    if train.empty or valid.empty or test.empty:
        raise ValueError("dataset must contain train / validation / test splits")
    return train, valid, test


def get_feature_columns(
    df: pd.DataFrame, override: Sequence[str] | None = None,
) -> list[str]:
    pool = override if override else DEFAULT_FEATURES
    keep: list[str] = []
    for c in pool:
        if c in df.columns and c not in LEAKAGE_COLUMNS:
            if pd.api.types.is_numeric_dtype(df[c]) or pd.api.types.is_bool_dtype(df[c]):
                keep.append(c)
    return keep


def clean_xy(
    df: pd.DataFrame, features: Sequence[str],
) -> tuple[pd.DataFrame, pd.Series]:
    X = df.loc[:, list(features)].copy()
    y = df["target"].astype(float).copy()
    X = X.replace([np.inf, -np.inf], np.nan)
    med = X.median(numeric_only=True)
    X = X.fillna(med).fillna(0)
    return X, y


# ── Metrics ───────────────────────────────────────────────────


def regression_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_true_arr = np.asarray(list(y_true), dtype=float)
    y_pred_arr = np.asarray(list(y_pred), dtype=float)
    mask = np.isfinite(y_true_arr) & np.isfinite(y_pred_arr)
    y_true_arr = y_true_arr[mask]
    y_pred_arr = y_pred_arr[mask]
    if not len(y_true_arr):
        return {"MAE": float("nan"), "RMSE": float("nan"), "WAPE": float("nan"), "R2": float("nan")}
    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr)))
    denom = float(np.sum(np.abs(y_true_arr)))
    wape = float(np.sum(np.abs(y_true_arr - y_pred_arr)) / denom) if denom else float("nan")
    try:
        r2 = float(r2_score(y_true_arr, y_pred_arr))
    except Exception:
        r2 = float("nan")
    return {"MAE": mae, "RMSE": rmse, "WAPE": wape, "R2": r2}


# ── Artifact path layout ──────────────────────────────────────


def artifact_dir(cfg: TrainingConfig, *, model_type: str, target_type: str = "price",
                 horizon: int | None = None) -> str:
    """Convention: ``{prefix}/{model_type}/{target_type}/h{horizon|none}/v{version}/``."""
    h = f"h{horizon}" if horizon is not None else "h_global"
    return f"{cfg.artifact_prefix}/{model_type}/{target_type}/{h}/{cfg.version}"


# ── Registry registration ────────────────────────────────────


def register_model(
    cfg: TrainingConfig,
    *,
    model_name: str,
    model_type: str,
    target_type: str,
    artifact_path: str,
    horizon: int | None = None,
    metrics: dict | None = None,
    feature_set_version: str | None = None,
    admin_token: str | None = None,
) -> dict | None:
    """POST to ``/api/v1/admin/models``. Requires an ADMIN-role Firebase token.

    Returns the created row or ``None`` on failure (logged). Promotion to
    ``is_active`` is intentionally a separate operator step.
    """
    import httpx

    payload = {
        "model_name": model_name,
        "model_type": model_type,
        "target_type": target_type,
        "version": cfg.version,
        "artifact_path": artifact_path,
        "horizon": horizon,
        "feature_set_version": feature_set_version,
        "metrics": metrics,
    }
    headers: dict[str, str] = {}
    token = admin_token or os.environ.get("ADMIN_FIREBASE_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{cfg.api_gateway_url.rstrip('/')}/api/v1/admin/models"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.exception("register_model failed; artifact still in MinIO at %s", artifact_path)
        return None


def save_metrics_local(metrics: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")


def setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


__all__ = [
    "DEFAULT_FEATURES",
    "LEAKAGE_COLUMNS",
    "TrainingConfig",
    "artifact_dir",
    "clean_xy",
    "download_parquet",
    "get_feature_columns",
    "get_minio_client",
    "load_dataset",
    "regression_metrics",
    "register_model",
    "save_metrics_local",
    "setup_logging",
    "split_dataset",
    "upload_file",
]
