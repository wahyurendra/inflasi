"""dim_calendar — add ML feature columns

Extends `dim_calendar` with day_of_week, quarter, month boundaries, and
Indonesian holiday windows used by the feature store.

Revision ID: 0003_calendar_features
Revises: 0002_feature_store
Create Date: 2026-05-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_calendar_features"
down_revision: Union[str, None] = "0002_feature_store"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLS = [
    ("day_of_week", sa.Integer()),
    ("week_of_year", sa.Integer()),
    ("quarter", sa.Integer()),
    ("is_month_start", sa.Boolean()),
    ("is_month_end", sa.Boolean()),
    ("ramadan_flag", sa.Boolean()),
    ("lebaran_minus_21", sa.Boolean()),
    ("lebaran_minus_14", sa.Boolean()),
    ("lebaran_minus_7", sa.Boolean()),
    ("lebaran_plus_7", sa.Boolean()),
    ("nataru_minus_14", sa.Boolean()),
    ("idul_adha_window", sa.Boolean()),
    ("school_holiday_flag", sa.Boolean()),
    ("harvest_flag", sa.Boolean()),
]


def upgrade() -> None:
    for name, col_type in _NEW_COLS:
        op.add_column("dim_calendar", sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_NEW_COLS):
        op.drop_column("dim_calendar", name)
