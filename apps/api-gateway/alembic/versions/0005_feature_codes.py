"""feature_store_daily — add *_code columns expected by the training pipeline

Adds the ten integer columns the training notebook (`forecast_models_combined.py`)
reads as features so inference & training see the same schema:

- commodity_id_code, region_id_code, entity_id_code  (CRC32 hash of the kode string)
- series_family_code, frequency_code, entity_level_code, unit_code  (fixed dict)
- series_key_code  (BIGINT composite hash over the natural grain)
- has_complete_weather, has_complete_macro  (int booleans)

Encoding is computed in `app.services.feature_encoder` and applied by both the
`FeatureBuilder` (online) and the `ml/training/` package (offline), so the same
input always maps to the same code.

Idempotent: ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.

Revision ID: 0005_feature_codes
Revises: 0004_forecasting_v2
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005_feature_codes"
down_revision: Union[str, None] = "0004_forecasting_v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLS: list[tuple[str, str]] = [
    ("commodity_id_code", "BIGINT"),
    ("region_id_code", "BIGINT"),
    ("entity_id_code", "BIGINT"),
    ("series_family_code", "INTEGER"),
    ("frequency_code", "INTEGER"),
    ("entity_level_code", "INTEGER"),
    ("unit_code", "INTEGER"),
    ("series_key_code", "BIGINT"),
    ("has_complete_weather", "INTEGER"),
    ("has_complete_macro", "INTEGER"),
]


def upgrade() -> None:
    for name, col_type in _NEW_COLS:
        op.execute(
            f"ALTER TABLE feature_store_daily ADD COLUMN IF NOT EXISTS {name} {col_type}"
        )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fs_series_key "
        "ON feature_store_daily (series_key_code)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_fs_series_key")
    for name, _ in _NEW_COLS:
        op.execute(f"ALTER TABLE feature_store_daily DROP COLUMN IF EXISTS {name}")
