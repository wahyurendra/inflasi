"""content_blog_posts — auto-generated daily blog articles

Stores public, SEO-facing blog posts narrating the day's food-price situation.
One row per (tanggal, tipe) so the daily analytics batch is idempotent —
re-running a date upserts rather than duplicating.

Revision ID: 0010_blog_posts
Revises: 0009_widen_region_code
Create Date: 2026-05-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_blog_posts"
down_revision: Union[str, None] = "0009_widen_region_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_blog_posts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("excerpt", sa.String(400), nullable=False, server_default=""),
        sa.Column("body_md", sa.Text, nullable=False),
        sa.Column("tipe", sa.String(20), nullable=False, server_default="harian"),
        sa.Column("status", sa.String(20), nullable=False, server_default="published"),
        sa.Column("tanggal", sa.Date, nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("data_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("model", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tanggal", "tipe", name="uq_blog_tanggal_tipe"),
        sa.UniqueConstraint("slug", name="uq_blog_slug"),
    )
    op.create_index(
        "ix_blog_status_published_at",
        "content_blog_posts",
        ["status", "published_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_blog_status_published_at", table_name="content_blog_posts")
    op.drop_table("content_blog_posts")
