"""widen dim_region.kode_wilayah

Slug-style codes used in `feature_store_daily` (e.g. `sumatera_utara`,
`kepulauan_bangka_belitung`, `nusa_tenggara_timur`) overflow the original
`VARCHAR(10)`. Widening to `VARCHAR(50)` keeps the column compatible with both
2-digit BPS codes and the canonical slugs.

Revision ID: 0009_widen_region_code
Revises: 0008_timescaledb_hypertables
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0009_widen_region_code"
down_revision: Union[str, None] = "0008_timescaledb_hypertables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE dim_region ALTER COLUMN kode_wilayah TYPE VARCHAR(50)")


def downgrade() -> None:
    op.execute("ALTER TABLE dim_region ALTER COLUMN kode_wilayah TYPE VARCHAR(10)")
