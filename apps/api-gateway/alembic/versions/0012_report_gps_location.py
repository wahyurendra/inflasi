"""report_gps_location — capture reporter's GPS coordinates with each report

Adds `price_reports.latitude`/`longitude` (nullable — GPS capture on the
report form is best-effort, not required to submit). Same precision as
`dim_region`/`dim_market`'s coordinate columns.

Revision ID: 0012_report_gps_location
Revises: 0011_gamification_award_guard
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_report_gps_location"
down_revision: Union[str, None] = "0011_gamification_award_guard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("price_reports", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("price_reports", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))


def downgrade() -> None:
    op.drop_column("price_reports", "longitude")
    op.drop_column("price_reports", "latitude")
