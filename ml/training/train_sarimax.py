"""Train SARIMAX per top-N series (order=(1,1,1), seasonal=(1,0,1,7))."""

from __future__ import annotations

import argparse
import logging
import warnings
from pathlib import Path

import joblib
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

warnings.filterwarnings("ignore")
logger = logging.getLogger("training.sarimax")

_EXOG = (
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window", "school_holiday_flag",
    "harvest_flag", "rainfall_1d", "temperature_avg", "rainfall_anomaly",
    "extreme_weather_flag", "inflation_mom_lag_1", "inflation_yoy_lag_1",
    "usd_idr_change", "bi_rate", "fuel_price_flag",
)
_MIN_TRAIN_DAYS = 365
_ORDER = (1, 1, 1)
_SEASONAL_ORDER = (1, 0, 1, 7)


def _prepare(df: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    out = df.sort_values("date").set_index("date")
    y_raw = pd.to_numeric(out["target"], errors="coerce")
    assert isinstance(y_raw, pd.Series)
    y = y_raw.asfreq("D").interpolate().ffill().bfill()
    exog_cols = [c for c in _EXOG if c in out.columns]
    ex_raw = out[exog_cols]
    assert isinstance(ex_raw, pd.DataFrame)
    ex = ex_raw.astype(float).replace([float("inf"), float("-inf")], None).asfreq("D").ffill().bfill().fillna(0)
    return y, ex


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--max-series", type=int, default=30)
    parser.add_argument("--no-register", action="store_true")
    args = parser.parse_args()

    setup_logging()
    cfg = TrainingConfig.from_env(horizon=args.horizon)
    local = download_parquet(cfg)
    df = load_dataset(local)
    train, valid, _ = split_dataset(df)

    series_keys = (
        train.groupby("series_key_code").size().sort_values(ascending=False).index.tolist()[: args.max_series]
    )

    from statsmodels.tsa.statespace.sarimax import SARIMAX

    base = artifact_dir(cfg, model_type="sarimax", horizon=None)
    cache = Path(cfg.local_cache) / "sarimax" / cfg.version
    cache.mkdir(parents=True, exist_ok=True)
    trained: dict[str, dict] = {}

    for key in series_keys:
        tr = train[train["series_key_code"].eq(key)]
        va = valid[valid["series_key_code"].eq(key)]
        if len(tr) < _MIN_TRAIN_DAYS or va.empty:
            continue
        try:
            tv = pd.concat([tr, va], axis=0)
            y_tv, ex_tv = _prepare(tv)
            fit_tv = SARIMAX(
                y_tv, exog=ex_tv,
                order=_ORDER, seasonal_order=_SEASONAL_ORDER,
                enforce_stationarity=False, enforce_invertibility=False,
            ).fit(disp=False, maxiter=100)
            local_path = cache / f"series_{key}.joblib"
            joblib.dump(fit_tv, local_path)
            upload_file(cfg, local_path, f"{base}/series_{key}.joblib")
            trained[str(key)] = {"aic": float(fit_tv.aic), "bic": float(fit_tv.bic)}
        except Exception as e:
            logger.warning("SARIMAX failed for series=%s: %s", key, e)

    metrics = {"trained_series": trained}
    save_metrics_local(metrics, cache / "metrics.json")
    logger.info("trained %s sarimax at %s", len(trained), base)

    if trained and not args.no_register:
        register_model(
            cfg,
            model_name="sarimax-per-series",
            model_type="sarimax",
            target_type="price",
            artifact_path=base,
            horizon=None,
            metrics={"trained_series_count": len(trained)},
        )


if __name__ == "__main__":
    main()
