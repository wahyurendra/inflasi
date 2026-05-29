"""Train Temporal Fusion Transformer with QuantileLoss([0.1, 0.5, 0.9]).

Requires the GPU image (``Dockerfile.gpu`` — installs torch + lightning +
pytorch-forecasting). Saves the best checkpoint to MinIO and registers
``model_type='tft'`` with ``horizon=<horizon>``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from ml.training.common import (
    TrainingConfig,
    artifact_dir,
    download_parquet,
    load_dataset,
    register_model,
    save_metrics_local,
    setup_logging,
    split_dataset,
    upload_file,
)

logger = logging.getLogger("training.tft")


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


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values(["series_key_code", "date"])
    out["time_idx"] = (out["date"] - out["date"].min()).dt.days.astype(int)
    out["series"] = out["series_key_code"].astype(str)
    for c in _STATIC_CATEGORICALS:
        if c in out.columns:
            out[c] = out[c].astype(str)
    for c in list(_KNOWN_REALS) + list(_OBSERVED_REALS) + ["target"]:
        if c in out.columns:
            col = pd.to_numeric(out[c], errors="coerce")
            assert isinstance(col, pd.Series)
            out[c] = col.replace([float("inf"), float("-inf")], None)
            out[c] = out.groupby("series")[c].transform(lambda s: s.ffill().bfill()).fillna(0)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--max-encoder-length", type=int, default=90)
    parser.add_argument("--max-epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--hidden-size", type=int, default=32)
    parser.add_argument("--no-register", action="store_true")
    args = parser.parse_args()

    setup_logging()
    cfg = TrainingConfig.from_env(horizon=args.horizon)

    import torch
    import lightning.pytorch as pl  # type: ignore
    from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint  # type: ignore
    from pytorch_forecasting import (  # type: ignore
        TemporalFusionTransformer,
        TimeSeriesDataSet,
    )
    from pytorch_forecasting.metrics import QuantileLoss  # type: ignore

    local = download_parquet(cfg)
    df = _prep(load_dataset(local))
    train, valid, _ = split_dataset(df)
    train_cutoff = int(train["time_idx"].max())

    known = [c for c in _KNOWN_REALS if c in df.columns]
    observed = [c for c in _OBSERVED_REALS if c in df.columns]
    static = [c for c in _STATIC_CATEGORICALS if c in df.columns]

    train_valid = pd.concat([train, valid], axis=0)
    training = TimeSeriesDataSet(
        train_valid[train_valid["time_idx"] <= train_cutoff],
        time_idx="time_idx",
        target="target",
        group_ids=["series"],
        max_encoder_length=args.max_encoder_length,
        max_prediction_length=args.horizon,
        static_categoricals=static,
        time_varying_known_reals=known,
        time_varying_unknown_reals=observed + ["target"],
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
        allow_missing_timesteps=True,
    )
    validation = TimeSeriesDataSet.from_dataset(
        training, train_valid, min_prediction_idx=train_cutoff + 1, stop_randomization=True,
    )

    cache = Path(cfg.local_cache) / "tft" / f"h{args.horizon}" / cfg.version
    cache.mkdir(parents=True, exist_ok=True)

    model = TemporalFusionTransformer.from_dataset(
        training,
        learning_rate=0.03,
        hidden_size=args.hidden_size,
        attention_head_size=4,
        dropout=0.1,
        hidden_continuous_size=16,
        loss=QuantileLoss(quantiles=[0.1, 0.5, 0.9]),
        optimizer="adam",
        reduce_on_plateau_patience=4,
    )

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=5, mode="min"),
        ModelCheckpoint(
            dirpath=str(cache), filename="tft-{epoch:02d}-{val_loss:.4f}",
            monitor="val_loss", mode="min", save_top_k=1,
        ),
    ]
    trainer = pl.Trainer(
        max_epochs=args.max_epochs,
        accelerator="gpu" if torch.cuda.is_available() else "cpu",
        devices=1,
        precision="bf16-mixed" if torch.cuda.is_available() else "32-true",
        callbacks=callbacks,
        gradient_clip_val=0.1,
        default_root_dir=str(cache),
    )
    trainer.fit(
        model,
        training.to_dataloader(train=True, batch_size=args.batch_size, num_workers=4),
        validation.to_dataloader(train=False, batch_size=args.batch_size, num_workers=4),
    )

    best = callbacks[-1].best_model_path
    if not best:
        logger.error("no best checkpoint produced")
        return
    base = artifact_dir(cfg, model_type="tft", horizon=args.horizon)
    remote_key = f"{base}/best.ckpt"
    upload_file(cfg, best, remote_key)
    save_metrics_local({"best_checkpoint_local": best, "remote_key": remote_key}, cache / "metrics.json")
    if not args.no_register:
        register_model(
            cfg,
            model_name=f"tft-h{args.horizon}",
            model_type="tft",
            target_type="price",
            artifact_path=remote_key,
            horizon=args.horizon,
        )


if __name__ == "__main__":
    main()
