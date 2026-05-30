"""Local LightGBM trainer — skips MinIO + Pink Sheet export step.

Pulls `feature_store_daily` directly from Postgres, trains point + p10/p50/p90
quantile models, writes joblibs to `/tmp/inflasi-models/...`, then INSERTs a
`model_registry` row pointing at that local directory.

Designed for the local-dev path described in `INFLASI_Real_Data_Init_Plan.md
§7` when MinIO isn't port-forwarded and the training image isn't installed.
The K8s training Job (`ml/training/train_lightgbm.py`) remains the production
path — that one uploads to MinIO and the ML gateway loads from there.

The `is_active=True` flag is *not* set here: promotion is a separate operator
decision via `POST /api/admin/models/{id}/promote`. Run with `--promote` to
auto-promote for smoke tests.

Usage:
    python -m scripts.train_lightgbm_local --horizon 7
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger("train_lightgbm_local")


# Feature columns: every numeric column from `feature_store_daily` that's
# safe to use at inference time. Excludes the target columns and identifier
# strings. Kept close to the production trainer's selection (mirrored from
# `ml/training/common.py:DEFAULT_FEATURES`) so swapping pipelines later
# doesn't shift the model surface.
FEATURES = [
    "price",
    "day_of_week", "week_of_year", "month", "quarter",
    "is_weekend", "is_month_start", "is_month_end",
    "ramadan_flag", "lebaran_minus_21", "lebaran_minus_14", "lebaran_minus_7",
    "lebaran_plus_7", "nataru_minus_14", "idul_adha_window",
    "school_holiday_flag", "harvest_flag",
    "price_lag_1", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_30",
    "rolling_std_7", "rolling_min_7", "rolling_max_7",
    "rolling_median_7", "rolling_median_30",
    "rainfall_1d", "temperature_avg", "rainfall_anomaly",
    "inflation_mom_lag_1", "inflation_yoy_lag_1",
    "usd_idr_change", "bi_rate", "fuel_price_flag",
    "data_quality_score",
    "commodity_id_code", "region_id_code", "series_key_code",
]

NUM_BOOST_ROUND = 1500
EARLY_STOPPING = 80
LEARNING_RATE = 0.05
NUM_LEAVES = 63
DEFAULT_ARTIFACT_ROOT = "/tmp/inflasi-models"


async def load_split(
    db: AsyncSession,
    *,
    split: str,
    target_col: str,
    features: list[str],
) -> pd.DataFrame:
    cols = ", ".join(set(features + [target_col]))
    rows = (await db.execute(
        text(f"""
            SELECT {cols}
            FROM feature_store_daily
            WHERE split = :split AND {target_col} IS NOT NULL
        """),
        {"split": split},
    )).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])


def _xy(df: pd.DataFrame, features: list[str], target: str):
    cols_present = [c for c in features if c in df.columns]
    X = df[cols_present].apply(pd.to_numeric, errors="coerce").fillna(0).astype("float32")
    y = pd.to_numeric(df[target], errors="coerce").astype("float32")
    mask = ~y.isna()
    return X.loc[mask], y.loc[mask], cols_present


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
        verbose=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="l1",
        callbacks=[lgb.early_stopping(EARLY_STOPPING), lgb.log_evaluation(0)],
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
        verbose=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="quantile",
        callbacks=[lgb.early_stopping(EARLY_STOPPING), lgb.log_evaluation(0)],
    )
    return model


def metrics(y_true, y_pred) -> dict[str, float]:
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    err = yp - yt
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err * err)))
    nz = np.abs(yt) > 1e-9
    mape = float(np.mean(np.abs(err[nz]) / np.abs(yt[nz])) * 100) if nz.any() else 0.0
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 4)}


async def register(
    db: AsyncSession,
    *,
    artifact_dir: Path,
    horizon: int,
    version: str,
    metrics_payload: dict,
    promote: bool,
) -> int:
    # If promoting, deactivate other rows in the same slot first.
    if promote:
        await db.execute(text("""
            UPDATE model_registry
               SET is_active = FALSE
             WHERE model_type = 'lightgbm'
               AND target_type = 'price'
               AND horizon = :h
        """), {"h": horizon})

    row = (await db.execute(
        text("""
            INSERT INTO model_registry
              (model_name, model_type, target_type, horizon, version,
               artifact_path, feature_set_version, metrics, params,
               training_start_date, training_end_date, is_active)
            VALUES
              (:name, 'lightgbm', 'price', :h, :version,
               :path, 'v1', CAST(:metrics AS JSONB), CAST(:params AS JSONB),
               :ts, :te, :is_active)
            RETURNING id
        """),
        {
            "name": f"lightgbm-h{horizon}",
            "h": horizon,
            "version": version,
            "path": str(artifact_dir),
            "metrics": json.dumps(metrics_payload),
            "params": json.dumps({
                "learning_rate": LEARNING_RATE,
                "num_leaves": NUM_LEAVES,
                "num_boost_round": NUM_BOOST_ROUND,
            }),
            "ts": metrics_payload.get("train_start"),
            "te": metrics_payload.get("train_end"),
            "is_active": bool(promote),
        },
    )).scalar()
    await db.commit()
    return int(row)


async def main(
    *,
    horizon: int,
    artifact_root: Path,
    promote: bool,
    version: str,
) -> None:
    url = _resolve_url()
    engine = create_async_engine(url, pool_recycle=300)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    target_col = f"target_h{horizon}"
    logger.info("loading splits for target=%s", target_col)

    async with factory() as db:
        train_df = await load_split(db, split="train", target_col=target_col, features=FEATURES)
        valid_df = await load_split(db, split="validation", target_col=target_col, features=FEATURES)
        test_df = await load_split(db, split="test", target_col=target_col, features=FEATURES)
    logger.info(
        "loaded train=%s valid=%s test=%s",
        len(train_df), len(valid_df), len(test_df),
    )
    if min(len(train_df), len(valid_df), len(test_df)) < 100:
        raise SystemExit("insufficient rows in one or more splits")

    X_train, y_train, used = _xy(train_df, FEATURES, target_col)
    X_valid, y_valid, _ = _xy(valid_df, used, target_col)
    X_test, y_test, _ = _xy(test_df, used, target_col)
    logger.info("training on %s features: %s", len(used), used[:8] + ["..."])

    out_dir = artifact_root / "lightgbm" / "price" / f"h{horizon}" / version
    out_dir.mkdir(parents=True, exist_ok=True)

    point = train_point(X_train, y_train, X_valid, y_valid)
    joblib.dump({"model": point, "features": used}, out_dir / "point.joblib")
    test_pred = point.predict(X_test)
    m = {
        "valid": metrics(y_valid, point.predict(X_valid)),
        "test": metrics(y_test, test_pred),
        "n_train": int(len(X_train)),
        "n_valid": int(len(X_valid)),
        "n_test": int(len(X_test)),
        "features_used": used,
        "train_start": _safe_date_from_df(train_df, "min"),
        "train_end": _safe_date_from_df(train_df, "max"),
    }
    logger.info("point metrics: %s", m["test"])

    for alpha, name in ((0.1, "p10"), (0.5, "p50"), (0.9, "p90")):
        q = train_quantile(X_train, y_train, X_valid, y_valid, alpha)
        joblib.dump({"model": q, "features": used, "alpha": alpha}, out_dir / f"quantile_{name}.joblib")
    (out_dir / "metrics.json").write_text(json.dumps(m, indent=2, default=str))
    logger.info("artifacts written to %s", out_dir)

    async with factory() as db:
        model_id = await register(
            db,
            artifact_dir=out_dir,
            horizon=horizon,
            version=version,
            metrics_payload=m,
            promote=promote,
        )
    logger.info("registered model_id=%s (promote=%s)", model_id, promote)
    await engine.dispose()


def _safe_date_from_df(df: pd.DataFrame, kind: str) -> str | None:
    """Pull the train/test date bounds when the dataframe carries `date`.
    The selected SELECT may have dropped it — return None when missing."""
    if "date" not in df.columns or df.empty:
        return None
    series = pd.to_datetime(df["date"], errors="coerce").dropna()
    if series.empty:
        return None
    target = series.min() if kind == "min" else series.max()
    return target.date().isoformat()


def _resolve_url() -> str:
    raw = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "postgresql+asyncpg://postgres:postgres@localhost:5432/inflasi"


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Train LightGBM locally (no MinIO).")
    parser.add_argument("--horizon", type=int, default=7, choices=[7, 14, 30])
    parser.add_argument("--artifact-root", default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--promote", action="store_true",
                        help="Mark the new model is_active=TRUE (smoke tests only).")
    parser.add_argument("--version", default=f"local-{date.today().isoformat()}")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(main(
        horizon=args.horizon,
        artifact_root=Path(args.artifact_root),
        promote=args.promote,
        version=args.version,
    ))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _cli()
