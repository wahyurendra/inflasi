"""Shared training utilities — dataset loading, metrics, GCS upload, registry POST.

Mirrors the helper functions in the user's notebook so the training scripts read
like simplified versions of it. Each ``train_*.py`` reads a parquet from GCS
(or the local cache), trains its model, writes the artifact(s) back to GCS,
then POSTs to ``/api/internal/models`` to register the new version. Promotion to
``is_active = true`` is a separate operator step (avoid auto-promote until
backtest confirms).
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse

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
    dataset_path: str = "gs://train-ml/datasets/train_ready_h7.parquet"
    artifact_prefix: str = "models"                         # GCS object prefix
    version: str = "v1"                                     # bump per training run
    api_gateway_url: str = "http://inflasi-api:8080"
    gcs_bucket: str = "train-ml"
    local_cache: str = "/tmp/inflasi-training"

    @classmethod
    def from_env(cls, *, horizon: int = 7) -> "TrainingConfig":
        bucket = _bucket_name(os.environ.get("GCS_BUCKET", "train-ml"))
        return cls(
            horizon=horizon,
            dataset_path=os.environ.get(
                "TRAIN_DATASET_PATH", f"gs://{bucket}/datasets/train_ready_h{horizon}.parquet"
            ),
            artifact_prefix=os.environ.get("ARTIFACT_PREFIX", "models"),
            version=os.environ.get("MODEL_VERSION", "v1"),
            api_gateway_url=os.environ.get("API_GATEWAY_URL", "http://inflasi-api:8080"),
            gcs_bucket=bucket,
            local_cache=os.environ.get("LOCAL_CACHE", "/tmp/inflasi-training"),
        )


# ── Google Cloud Storage helpers ──────────────────────────────


def _bucket_name(value: str) -> str:
    """Accept ``train-ml`` or ``gs://train-ml`` and return the bucket name."""
    raw = value.strip().rstrip("/")
    if raw.startswith("gs://"):
        parsed = urlparse(raw)
        if parsed.path not in {"", "/"}:
            raise ValueError("GCS_BUCKET must not include an object prefix")
        raw = parsed.netloc
    if not raw or raw in {".", ".."} or "/" in raw:
        raise ValueError(f"invalid GCS bucket: {value!r}")
    return raw


def split_gcs_location(value: str, default_bucket: str) -> tuple[str, str]:
    """Resolve a ``gs://bucket/key`` URI or relative object key."""
    raw = value.strip()
    if raw.startswith("gs://"):
        parsed = urlparse(raw)
        bucket = _bucket_name(parsed.netloc)
        key = parsed.path.lstrip("/")
    else:
        bucket = _bucket_name(default_bucket)
        key = raw.lstrip("/")
    if not key or any(part == ".." for part in Path(key).parts):
        raise ValueError(f"invalid GCS object path: {value!r}")
    return bucket, key


def gcs_uri(cfg: TrainingConfig, value: str) -> str:
    bucket, key = split_gcs_location(value, cfg.gcs_bucket)
    return f"gs://{bucket}/{key}"


def get_gcs_client():
    """Return a GCS client authenticated through Application Default Credentials."""
    from google.cloud import storage  # type: ignore

    return storage.Client()


def download_file(cfg: TrainingConfig, location: str) -> Path:
    """Download a GCS object into the persistent local cache when missing."""
    bucket, key = split_gcs_location(location, cfg.gcs_bucket)
    local = Path(cfg.local_cache) / "gcs" / bucket / key
    local.parent.mkdir(parents=True, exist_ok=True)
    if not local.exists() or local.stat().st_size == 0:
        temporary = local.with_name(f".{local.name}.{uuid.uuid4().hex}.part")
        try:
            blob = get_gcs_client().bucket(bucket).blob(key)
            blob.download_to_filename(str(temporary))
            temporary.replace(local)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return local


def download_parquet(cfg: TrainingConfig, key: str | None = None) -> Path:
    """Download a parquet from GCS; return the local cached path."""
    return download_file(cfg, key or cfg.dataset_path)


def upload_file(cfg: TrainingConfig, local_path: str | Path, key: str) -> str:
    """Upload a file to GCS and return its canonical ``gs://`` URI."""
    bucket, object_key = split_gcs_location(key, cfg.gcs_bucket)
    get_gcs_client().bucket(bucket).blob(object_key).upload_from_filename(str(local_path))
    return f"gs://{bucket}/{object_key}"


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
    """Return the canonical GCS directory URI for a model artifact set."""
    h = f"h{horizon}" if horizon is not None else "h_global"
    key = f"{cfg.artifact_prefix}/{model_type}/{target_type}/{h}/{cfg.version}"
    return gcs_uri(cfg, key)


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
    service_token: str | None = None,
) -> dict | None:
    """POST to the internal registry using the stable training service token.

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
    token = service_token or os.environ.get("TRAINING_SERVICE_TOKEN", "")
    if not token:
        logger.error(
            "TRAINING_SERVICE_TOKEN missing; artifact remains in GCS at %s",
            artifact_path,
        )
        return None
    headers = {"X-Training-Token": token}
    url = f"{cfg.api_gateway_url.rstrip('/')}/api/internal/models"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.exception("register_model failed; artifact still in GCS at %s", artifact_path)
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
    "download_file",
    "download_parquet",
    "gcs_uri",
    "get_feature_columns",
    "get_gcs_client",
    "load_dataset",
    "regression_metrics",
    "register_model",
    "save_metrics_local",
    "setup_logging",
    "split_dataset",
    "split_gcs_location",
    "upload_file",
]
