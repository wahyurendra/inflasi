"""gamification_award_guard — idempotency marker for report-approval awards

Adds `price_reports.gamification_awarded_at`, claimed via an atomic conditional
UPDATE the first (and only the first) time a report transitions to APPROVED, so
points/streak/badges are never awarded twice for the same report.

Revision ID: 0011_gamification_award_guard
Revises: 0010_blog_posts
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_gamification_award_guard"
down_revision: Union[str, None] = "0010_blog_posts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "price_reports",
        sa.Column("gamification_awarded_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("price_reports", "gamification_awarded_at")
