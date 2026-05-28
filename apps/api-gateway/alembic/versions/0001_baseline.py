"""baseline — create all tables from SQLAlchemy metadata

Bootstrap migration for an empty database. Creates every table defined in
app/models/tables.py via metadata.create_all (no autogenerate / live DB needed to
author it). Subsequent schema changes use `alembic revision --autogenerate`.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.database import Base
import app.models.tables  # noqa: F401  (registers all tables on Base.metadata)

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # User.role / PriceReport.status use create_type=False — we own type creation here.
    bind.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE "UserRole" AS ENUM ('ADMIN', 'GOVERNMENT_ANALYST', 'CONTRIBUTOR', 'REPORTER');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))
    bind.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE "ReportStatus" AS ENUM ('PENDING', 'APPROVED', 'FLAGGED', 'REJECTED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    bind.execute(sa.text('DROP TYPE IF EXISTS "ReportStatus"'))
    bind.execute(sa.text('DROP TYPE IF EXISTS "UserRole"'))
