"""Shared feature encoder — deterministic *_code columns for the ML pipeline.

Used by:
- :mod:`app.services.feature_builder` to populate ``feature_store_daily`` at
  inference time.
- ``ml/training/`` scripts to emit ``train_ready_h{7,14,30}.parquet`` with the
  identical encoding.

Keeping a single implementation eliminates "training/serving skew": the same
``commodity_id`` string maps to the same ``commodity_id_code`` integer whether
seen by the trainer or by ml-gateway at request time. No persisted
LabelEncoder state to manage.

Encoding rules
--------------
* String kodes (``commodity_id``, ``region_id``, ``entity_id``) → stable
  ``crc32`` mod 2**31 (positive int32). Sufficient uniqueness at our cardinality
  (~50 commodities × 34 provinces).
* Small fixed-domain categoricals (``entity_level``, ``frequency``,
  ``series_family``, ``unit``) → fixed dictionary lookup; unknowns → 0.
* ``series_key_code`` → 64-bit composite hash of
  ``f"{commodity_id}|{region_id}|{entity_level}"``.
* ``has_complete_weather`` / ``has_complete_macro`` → boolean AND over the
  relevant raw columns, cast to int.
"""

from __future__ import annotations

import zlib
from typing import Any

import pandas as pd

ENTITY_LEVEL_CODES: dict[str, int] = {
    "province": 1,
    "provinsi": 1,
    "kabupaten": 2,
    "kab_kota": 2,
    "national": 3,
    "nasional": 3,
}

FREQUENCY_CODES: dict[str, int] = {
    "daily": 1,
    "weekly": 2,
    "monthly": 3,
}

SERIES_FAMILY_CODES: dict[str, int] = {
    "daily_province": 1,
    "daily_kabupaten": 2,
    "daily_national": 3,
    "daily_other": 9,
}

# Common units — extend as needed. Unknown units fall through to 0.
UNIT_CODES: dict[str, int] = {
    "kg": 1,
    "Kg": 1,
    "KG": 1,
    "liter": 2,
    "Liter": 2,
    "L": 2,
    "butir": 3,
    "ekor": 4,
    "ikat": 5,
    "biji": 6,
    "ons": 7,
    "ton": 8,
}


def _hash32(value: Any) -> int:
    """Stable, positive int32 hash. ``None`` / NaN → 0."""
    if value is None:
        return 0
    if isinstance(value, float) and pd.isna(value):
        return 0
    s = str(value)
    if not s:
        return 0
    return zlib.crc32(s.encode("utf-8")) & 0x7FFFFFFF


def _hash64(value: str) -> int:
    """Stable 63-bit hash by concatenating two crc32s. Fits in BIGINT positive range."""
    if not value:
        return 0
    encoded = value.encode("utf-8")
    high = zlib.crc32(b"H|" + encoded) & 0xFFFFFFFF
    low = zlib.crc32(b"L|" + encoded) & 0xFFFFFFFF
    return ((high << 31) | low) & 0x7FFFFFFFFFFFFFFF


def _col(df: pd.DataFrame, name: str, default: Any = None) -> pd.Series:
    """Return ``df[name]`` or a Series of ``default`` of matching length."""
    if name in df.columns:
        col = df[name]
        if isinstance(col, pd.Series):
            return col
    return pd.Series([default] * len(df), index=df.index)


def encode_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Add the ten *_code columns the training notebook expects.

    Operates in place — returns the same DataFrame for chaining. Idempotent:
    re-running on an already-encoded frame produces identical values.
    """
    # ID hashes. Accept either the `*_id` names (training parquet) or the
    # `*_kode` names (serving path before rename) so a column-naming slip in one
    # caller can't crash the encoder — and the analytics batch — outright.
    commodity_ids = _col(df, "commodity_id")
    if commodity_ids.isna().all() and "commodity_kode" in df.columns:
        commodity_ids = df["commodity_kode"]
    region_ids = _col(df, "region_id")
    if region_ids.isna().all() and "region_kode" in df.columns:
        region_ids = df["region_kode"]
    df["commodity_id_code"] = commodity_ids.map(_hash32).astype("int64")
    df["region_id_code"] = region_ids.map(_hash32).astype("int64")
    if "entity_id" in df.columns:
        df["entity_id_code"] = df["entity_id"].map(_hash32).astype("int64")
    else:
        df["entity_id_code"] = df["region_id_code"]

    # Fixed-domain categoricals
    df["entity_level_code"] = (
        _col(df, "entity_level", "")
        .astype(str)
        .map(lambda v: ENTITY_LEVEL_CODES.get(v, 0))
        .astype("int64")
    )
    df["frequency_code"] = (
        _col(df, "frequency", "daily")
        .astype(str)
        .map(lambda v: FREQUENCY_CODES.get(v, 0))
        .astype("int64")
    )
    df["series_family_code"] = (
        _col(df, "series_family", "")
        .astype(str)
        .map(lambda v: SERIES_FAMILY_CODES.get(v, 0))
        .astype("int64")
    )
    df["unit_code"] = (
        _col(df, "unit", "")
        .astype(str)
        .map(lambda v: UNIT_CODES.get(v, 0))
        .astype("int64")
    )

    # Series key — composite over the natural grain
    def _series_key(row: pd.Series) -> int:
        return _hash64(
            f"{row.get('commodity_id', '')}|"
            f"{row.get('region_id', '')}|"
            f"{row.get('entity_level', '')}"
        )

    df["series_key_code"] = df.apply(_series_key, axis=1).astype("int64")

    # Completeness flags
    df["has_complete_weather"] = (
        _col(df, "rainfall_1d").notna() & _col(df, "temperature_avg").notna()
    ).astype("int64")
    df["has_complete_macro"] = (
        _col(df, "usd_idr_change").notna() & _col(df, "inflation_mom_lag_1").notna()
    ).astype("int64")

    return df


CODE_COLUMNS: tuple[str, ...] = (
    "commodity_id_code",
    "region_id_code",
    "entity_id_code",
    "series_family_code",
    "frequency_code",
    "entity_level_code",
    "unit_code",
    "series_key_code",
    "has_complete_weather",
    "has_complete_macro",
)
