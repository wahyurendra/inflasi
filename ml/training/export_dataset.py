"""Export training-ready parquets from feature_store_daily.

Reads via the api-gateway's CSV export endpoint (no direct DB access from this
package), pivots the wide ``target_h{7,14,30}`` columns into one long parquet
per horizon, applies :func:`encoder.encode_codes` to fill any missing *_code
columns (idempotent — feature_builder already wrote them at materialization
time), and uploads to MinIO at ``datasets/train_ready_h{horizon}.parquet``.

Run as a K8s Job; expects MinIO + api-gateway env vars.
"""

from __future__ import annotations

import argparse
import io
import logging
from pathlib import Path

import httpx
import pandas as pd

from ml.training.common import (
    TrainingConfig,
    get_minio_client,
    save_metrics_local,
    setup_logging,
)
from ml.training.encoder import encode_codes

logger = logging.getLogger("training.export_dataset")


def fetch_feature_store_csv(cfg: TrainingConfig) -> pd.DataFrame:
    url = f"{cfg.api_gateway_url.rstrip('/')}/api/v1/forecast/dataset/export"
    with httpx.Client(timeout=600.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        text = resp.text
    return pd.read_csv(io.StringIO(text))


def to_horizon_parquet(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    target_col = f"target_h{horizon}"
    if target_col not in df.columns:
        raise KeyError(f"{target_col} missing from feature_store_daily export")
    out = df[df[target_col].notna()].copy()
    out["target"] = out[target_col].astype(float)
    out["forecast_horizon_days"] = horizon
    # Drop the other horizons so the trainer sees a single supervised target.
    drop = [c for c in ("target_h7", "target_h14", "target_h30") if c in out.columns]
    out = out.drop(columns=drop)
    return encode_codes(out)


def upload_parquet(cfg: TrainingConfig, df: pd.DataFrame, horizon: int) -> str:
    local = Path(cfg.local_cache) / f"train_ready_h{horizon}.parquet"
    local.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(local, index=False)
    key = f"datasets/train_ready_h{horizon}.parquet"
    client = get_minio_client(cfg)
    client.fput_object(cfg.minio_datasets_bucket, key, str(local))
    return key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", nargs="+", type=int, default=[7, 14, 30])
    args = parser.parse_args()

    setup_logging()
    cfg = TrainingConfig.from_env()
    logger.info("fetching feature_store_daily export from %s", cfg.api_gateway_url)
    raw = fetch_feature_store_csv(cfg)
    logger.info("loaded %s rows × %s cols", len(raw), len(raw.columns))

    summary: dict[str, dict] = {}
    for h in args.horizons:
        df = to_horizon_parquet(raw, h)
        key = upload_parquet(cfg, df, h)
        summary[str(h)] = {"rows": int(len(df)), "minio_key": key}
        logger.info("uploaded h=%s → %s (%s rows)", h, key, len(df))

    save_metrics_local(summary, Path(cfg.local_cache) / "export_summary.json")


if __name__ == "__main__":
    main()
