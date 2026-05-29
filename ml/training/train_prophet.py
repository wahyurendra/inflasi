"""Train Prophet per series (top-N by row count). Single global horizon.

Outputs one ``series_{key}.joblib`` per trained series under
``models/prophet/price/h_global/v{version}/``. Stores predictions for the
validation/test split alongside so the stacking trainer can pick them up.
"""

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
logger = logging.getLogger("training.prophet")

_REGRESSORS = (
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window", "school_holiday_flag",
    "harvest_flag", "rainfall_1d", "temperature_avg", "rainfall_anomaly",
    "extreme_weather_flag", "inflation_mom_lag_1", "inflation_yoy_lag_1",
    "usd_idr_change", "bi_rate", "fuel_price_flag",
)
_MIN_TRAIN_DAYS = 365
_INTERVAL_WIDTH = 0.80


def _make_frame(df: pd.DataFrame, regressors: list[str]) -> pd.DataFrame:
    cols = ["date", "target"] + regressors
    out = df.sort_values("date").loc[:, cols].copy()
    out = out.rename(columns={"date": "ds", "target": "y"})
    for c in regressors:
        col = pd.to_numeric(out[c], errors="coerce")
        assert isinstance(col, pd.Series)
        out[c] = col.replace([float("inf"), float("-inf")], 0).fillna(0)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--max-series", type=int, default=30)
    parser.add_argument("--no-register", action="store_true")
    args = parser.parse_args()

    setup_logging()
    cfg = TrainingConfig.from_env(horizon=args.horizon)
    local_parquet = download_parquet(cfg)
    df = load_dataset(local_parquet)
    train, valid, test = split_dataset(df)

    regressors = [c for c in _REGRESSORS if c in df.columns]
    series_keys = (
        train.groupby("series_key_code").size().sort_values(ascending=False).index.tolist()[: args.max_series]
    )

    from prophet import Prophet

    base = artifact_dir(cfg, model_type="prophet", horizon=None)
    cache = Path(cfg.local_cache) / "prophet" / cfg.version
    cache.mkdir(parents=True, exist_ok=True)
    trained: dict[str, dict] = {}

    for key in series_keys:
        tr = train[train["series_key_code"].eq(key)]
        va = valid[valid["series_key_code"].eq(key)]
        te = test[test["series_key_code"].eq(key)]
        if len(tr) < _MIN_TRAIN_DAYS or va.empty or te.empty:
            continue
        try:
            tv_frame = _make_frame(pd.concat([tr, va], axis=0), regressors)
            m = Prophet(
                weekly_seasonality=True, yearly_seasonality=True,
                daily_seasonality=False, interval_width=_INTERVAL_WIDTH,
            )
            for r in regressors:
                m.add_regressor(r)
            m.fit(tv_frame)
            local = cache / f"series_{key}.joblib"
            joblib.dump(m, local)
            upload_file(cfg, local, f"{base}/series_{key}.joblib")
            trained[str(key)] = {"train_rows": int(len(tr) + len(va))}
        except Exception as e:
            logger.warning("Prophet failed for series=%s: %s", key, e)

    metrics = {"trained_series": trained, "regressors": regressors}
    save_metrics_local(metrics, cache / "metrics.json")
    logger.info("trained %s prophets at %s", len(trained), base)

    if trained and not args.no_register:
        register_model(
            cfg,
            model_name="prophet-per-series",
            model_type="prophet",
            target_type="price",
            artifact_path=base,
            horizon=None,
            metrics={"trained_series_count": len(trained)},
        )


if __name__ == "__main__":
    main()
