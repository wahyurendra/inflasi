"""market dimension — dim_market + market_id on price_reports and fact_price_daily

Tracks the physical market where a crowdsourced price was recorded. The crowd
flow today writes a free-text `nama_pasar` straight into `price_reports`; that
column stays for backwards compatibility, and `market_normalizer` fuzzy-maps
it to a `dim_market.id` whenever possible. `fact_price_daily.market_id` is
populated only for crowd rows — official PIHPS rows leave it NULL.

Idempotent: CREATE TABLE / ADD COLUMN / CREATE INDEX all use IF NOT EXISTS.

Revision ID: 0006_market_dimension
Revises: 0005_feature_codes
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0006_market_dimension"
down_revision: Union[str, None] = "0005_feature_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS dim_market (
            id BIGSERIAL PRIMARY KEY,
            region_id INTEGER NOT NULL REFERENCES dim_region(id),
            kode_pasar VARCHAR(50),
            nama_pasar VARCHAR(200) NOT NULL,
            tipe_pasar VARCHAR(50),
            alamat TEXT,
            latitude NUMERIC(10,7),
            longitude NUMERIC(10,7),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (region_id, nama_pasar)
        )
    """)

    # Hot path: lookup by region.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dim_market_region ON dim_market (region_id)"
    )
    # Case-insensitive lookup for the normalizer's exact-match probe.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dim_market_nama_lower "
        "ON dim_market ((LOWER(nama_pasar)))"
    )

    op.execute(
        "ALTER TABLE price_reports "
        "ADD COLUMN IF NOT EXISTS market_id BIGINT REFERENCES dim_market(id)"
    )
    op.execute(
        "ALTER TABLE fact_price_daily "
        "ADD COLUMN IF NOT EXISTS market_id BIGINT REFERENCES dim_market(id)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_price_reports_market "
        "ON price_reports (market_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fact_price_daily_market "
        "ON fact_price_daily (market_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_fact_price_daily_market")
    op.execute("DROP INDEX IF EXISTS idx_price_reports_market")
    op.execute("ALTER TABLE fact_price_daily DROP COLUMN IF EXISTS market_id")
    op.execute("ALTER TABLE price_reports DROP COLUMN IF EXISTS market_id")
    op.execute("DROP INDEX IF EXISTS idx_dim_market_nama_lower")
    op.execute("DROP INDEX IF EXISTS idx_dim_market_region")
    op.execute("DROP TABLE IF EXISTS dim_market")
