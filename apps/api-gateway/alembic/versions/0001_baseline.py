"""baseline — create all tables from SQLAlchemy metadata

Bootstrap migration for an empty database. Creates every table defined in
app/models/tables.py via metadata.create_all (no autogenerate / live DB needed to
author it). Subsequent schema changes use `alembic revision --autogenerate`.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op

from app.database import Base
import app.models.tables  # noqa: F401  (registers all tables on Base.metadata)

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
