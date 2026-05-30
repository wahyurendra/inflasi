"""timescaledb hypertables — convert time-series tables when the extension exists

Guarded by `pg_extension` lookup so this migration is safe to run on a plain
PostgreSQL instance (it becomes a no-op). On TimescaleDB it:

* Rewrites the PRIMARY KEY on each fact / analytics table to include the time
  column. TimescaleDB requires every UNIQUE/PK constraint to include the
  partitioning column.
* Calls `create_hypertable(..., if_not_exists => TRUE)` for each table.

Tables converted (idempotent — re-running has no effect):

* `fact_price_daily`     ↦ `tanggal`
* `fact_climate`         ↦ `tanggal`
* `feature_store_daily`  ↦ `date`
* `analytics_forecast`   ↦ `tanggal`
* `analytics_anomaly`    ↦ `tanggal`
* `analytics_risk_score` ↦ `tanggal`

NOT converted (low volume / non-time): dim_*, model_registry, model_training_runs,
forecast_model_components, forecast_backtest_results.

Compression policies are NOT installed here — that's a deliberate operator
decision (rate of ingest, query patterns). Apply via psql after volume justifies it.

Revision ID: 0008_timescaledb_hypertables
Revises: 0007_feature_store_monthly
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0008_timescaledb_hypertables"
down_revision: Union[str, None] = "0007_feature_store_monthly"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, time_col) pairs.
_HYPERTABLES: list[tuple[str, str]] = [
    ("fact_price_daily", "tanggal"),
    ("fact_climate", "tanggal"),
    ("feature_store_daily", "date"),
    ("analytics_forecast", "tanggal"),
    ("analytics_anomaly", "tanggal"),
    ("analytics_risk_score", "tanggal"),
]


_ENSURE_PK_INCLUDES_TIME = """
DO $$
DECLARE
    pk_name TEXT;
    pk_cols TEXT;
BEGIN
    SELECT con.conname,
           array_to_string(array_agg(att.attname ORDER BY ordinal), ',')
      INTO pk_name, pk_cols
      FROM pg_constraint con
      JOIN unnest(con.conkey) WITH ORDINALITY AS k(attnum, ordinal) ON TRUE
      JOIN pg_attribute att
        ON att.attrelid = con.conrelid AND att.attnum = k.attnum
     WHERE con.conrelid = '{table}'::regclass
       AND con.contype = 'p'
     GROUP BY con.conname;

    IF pk_cols IS NULL THEN
        RETURN; -- no PK on this table
    END IF;

    IF position('{time_col}' in pk_cols) = 0 THEN
        EXECUTE format('ALTER TABLE {table} DROP CONSTRAINT %I', pk_name);
        EXECUTE format(
            'ALTER TABLE {table} ADD CONSTRAINT {table}_pkey PRIMARY KEY (%s, {time_col})',
            pk_cols
        );
    END IF;
END $$;
"""


def _sql(s):
    """Tiny helper to avoid importing sqlalchemy.text into the module top."""
    from sqlalchemy import text

    return text(s)


def upgrade() -> None:
    bind = op.get_bind()

    has_timescale = bind.execute(
        _sql("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
    ).first() is not None
    if not has_timescale:
        # Soft skip: leave a NOTICE in the migration log; nothing to do.
        op.execute(
            "DO $$ BEGIN RAISE NOTICE "
            "'timescaledb extension not present; 0008 migration skipped'; END $$"
        )
        return

    # Inbound FK that depends on analytics_forecast(id). The PK rewrite below
    # would fail with "cannot drop constraint ... because other objects depend
    # on it" unless we drop the dependent FK first. We don't recreate it: under
    # TimescaleDB, FK targets must include the partitioning column, and the
    # components table doesn't carry the target date. Application code
    # (`ForecastRepo.replace_components`) already wipes-and-rewrites components
    # before each forecast upsert, so the integrity loss is bounded.
    op.execute(
        "ALTER TABLE forecast_model_components "
        "DROP CONSTRAINT IF EXISTS forecast_model_components_forecast_id_fkey"
    )

    for table, time_col in _HYPERTABLES:
        # Make sure the PK includes the time column.
        op.execute(_ENSURE_PK_INCLUDES_TIME.format(table=table, time_col=time_col))
        # Convert in-place. `migrate_data => TRUE` so existing rows get chunked.
        op.execute(
            f"SELECT create_hypertable("
            f"'{table}', '{time_col}', "
            f"if_not_exists => TRUE, migrate_data => TRUE"
            f")"
        )


def downgrade() -> None:
    # No-op downgrade. Reversing a hypertable conversion in place is destructive
    # (the chunk layout would need to be flattened back to a regular table) and
    # not worth automating — recover via backup if it really needs to roll back.
    pass
