"""dim_calendar — add ML feature columns

Extends `dim_calendar` with day_of_week, quarter, month boundaries, and
Indonesian holiday windows used by the feature store.

Idempotent: uses ADD COLUMN IF NOT EXISTS because tables.py already includes
these columns, so 0001_baseline's metadata.create_all may have created them
on a fresh install.

Revision ID: 0003_calendar_features
Revises: 0002_feature_store
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003_calendar_features"
down_revision: Union[str, None] = "0002_feature_store"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLS: list[tuple[str, str]] = [
    ("day_of_week", "INTEGER"),
    ("week_of_year", "INTEGER"),
    ("quarter", "INTEGER"),
    ("is_month_start", "BOOLEAN"),
    ("is_month_end", "BOOLEAN"),
    ("ramadan_flag", "BOOLEAN"),
    ("lebaran_minus_21", "BOOLEAN"),
    ("lebaran_minus_14", "BOOLEAN"),
    ("lebaran_minus_7", "BOOLEAN"),
    ("lebaran_plus_7", "BOOLEAN"),
    ("nataru_minus_14", "BOOLEAN"),
    ("idul_adha_window", "BOOLEAN"),
    ("school_holiday_flag", "BOOLEAN"),
    ("harvest_flag", "BOOLEAN"),
]


def upgrade() -> None:
    for name, col_type in _NEW_COLS:
        op.execute(f'ALTER TABLE dim_calendar ADD COLUMN IF NOT EXISTS {name} {col_type}')


def downgrade() -> None:
    for name, _ in reversed(_NEW_COLS):
        op.execute(f'ALTER TABLE dim_calendar DROP COLUMN IF EXISTS {name}')
