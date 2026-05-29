"""Train LightGBM point + p10/p50/p90 quantile models for a single horizon.

Outputs four joblibs to MinIO under ``models/lightgbm/price/h{horizon}/v{version}/``:
``point.joblib``, ``quantile_p10.joblib``, ``quantile_p50.joblib``,
``quantile_p90.joblib``. Each contains
``{"model": LGBMRegressor, "features": list[str], "alpha"?: float}``.

Registers the model_type=lightgbm row in model_registry with the directory path
as ``artifact_path`` so the loader can fetch all four files from one base URL.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import joblib

from ml.training.common import (
    TrainingConfig,
    artifact_dir,
    clean_xy,
    download_parquet,
    get_feature_columns,
    load_dataset,
    regression_metrics,
    register_model,
    save_metrics_local,
    setup_logging,
    split_dataset,
    upload_file,
)

logger = logging.getLogger("training.lightgbm")

NUM_BOOST_ROUND = 3000
EARLY_STOPPING = 100
LEARNING_RATE = 0.03
NUM_LEAVES = 63


def train_point(X_train, y_train, X_valid, y_valid):
    import lightgbm as lgb

    model = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=NUM_BOOST_ROUND,
        learning_rate=LEARNING_RATE,
        num_leaves=NUM_LEAVES,
        feature_fraction=0.85,
        bagging_fraction=0.85,
        bagging_freq=1,
        min_data_in_leaf=50,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="l1",
        callbacks=[lgb.early_stopping(EARLY_STOPPING), lgb.log_evaluation(200)],
    )
    return model


def train_quantile(X_train, y_train, X_valid, y_valid, alpha: float):
    import lightgbm as lgb

    model = lgb.LGBMRegressor(
        objective="quantile",
        alpha=alpha,
        n_estimators=NUM_BOOST_ROUND,
        learning_rate=LEARNING_RATE,
        num_leaves=NUM_LEAVES,
        feature_fraction=0.85,
        bagging_fraction=0.85,
        bagging_freq=1,
        min_data_in_leaf=50,
        random_state=42 + int(alpha * 100),
        n_jobs=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="quantile",
        callbacks=[lgb.early_stopping(EARLY_STOPPING), lgb.log_evaluation(200)],
    )
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--no-register", action="store_true")
    args = parser.parse_args()

    setup_logging()
    cfg = TrainingConfig.from_env(horizon=args.horizon)

    local_parquet = download_parquet(cfg)
    df = load_dataset(local_parquet)
    train, valid, test = split_dataset(df)
    features = get_feature_columns(df)
    logger.info(
        "lightgbm h=%s train=%s valid=%s test=%s features=%s",
        args.horizon, len(train), len(valid), len(test), len(features),
    )

    X_train, y_train = clean_xy(train, features)
    X_valid, y_valid = clean_xy(valid, features)
    X_test, y_test = clean_xy(test, features)

    cache = Path(cfg.local_cache) / "lightgbm" / f"h{args.horizon}" / cfg.version
    cache.mkdir(parents=True, exist_ok=True)
    base = artifact_dir(cfg, model_type="lightgbm", horizon=args.horizon)

    # Point model
    point = train_point(X_train, y_train, X_valid, y_valid)
    point_path = cache / "point.joblib"
    joblib.dump({"model": point, "features": features}, point_path)
    upload_file(cfg, point_path, f"{base}/point.joblib")

    test_pred = point.predict(X_test)
    metrics = {
        "valid": regression_metrics(y_valid, point.predict(X_valid)),
        "test": regression_metrics(y_test, test_pred),
    }

    # Quantile models
    for alpha, name in [(0.1, "p10"), (0.5, "p50"), (0.9, "p90")]:
        q = train_quantile(X_train, y_train, X_valid, y_valid, alpha)
        qpath = cache / f"quantile_{name}.joblib"
        joblib.dump({"model": q, "features": features, "alpha": alpha}, qpath)
        upload_file(cfg, qpath, f"{base}/quantile_{name}.joblib")

    save_metrics_local(metrics, cache / "metrics.json")

    if not args.no_register:
        register_model(
            cfg,
            model_name=f"lightgbm-h{args.horizon}",
            model_type="lightgbm",
            target_type="price",
            artifact_path=base,
            horizon=args.horizon,
            metrics=metrics,
        )
    logger.info("done; artifacts at %s", base)


if __name__ == "__main__":
    main()
