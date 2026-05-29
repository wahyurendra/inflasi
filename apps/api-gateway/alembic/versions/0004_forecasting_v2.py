"""forecasting v2 — quantile forecast, model registry, training runs, components

Adds support for ensemble-quantile forecasting:
- Upgrades `analytics_forecast` with p10/p50/p90, confidence, drivers, components.
- Introduces `model_registry` (versioned active models per model_type/target/horizon).
- Introduces `model_training_runs` (training audit trail).
- Introduces `forecast_model_components` (per base-model contribution to each forecast).
- Introduces `forecast_backtest_results` (historical evaluation per model+horizon+pair).

Idempotent: all ADD COLUMN / CREATE TABLE use IF NOT EXISTS. Existing rows in
`analytics_forecast` continue to work — new columns are nullable.

Revision ID: 0004_forecasting_v2
Revises: 0003_calendar_features
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_forecasting_v2"
down_revision: Union[str, None] = "0003_calendar_features"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FORECAST_NEW_COLS: list[tuple[str, str]] = [
    ("forecast_date", "DATE"),
    ("target_date", "DATE"),
    ("p10", "NUMERIC(12,2)"),
    ("p50", "NUMERIC(12,2)"),
    ("p90", "NUMERIC(12,2)"),
    ("confidence_score", "NUMERIC(6,4)"),
    ("risk_level", "VARCHAR(20)"),
    ("top_drivers", "JSONB"),
    ("model_contribution", "JSONB"),
    ("prediction_interval", "JSONB"),
    ("model_run_id", "BIGINT"),
    ("target_type", "VARCHAR(50)"),
]


def upgrade() -> None:
    for name, col_type in _FORECAST_NEW_COLS:
        op.execute(f"ALTER TABLE analytics_forecast ADD COLUMN IF NOT EXISTS {name} {col_type}")

    op.execute("""
        CREATE TABLE IF NOT EXISTS model_registry (
            id BIGSERIAL PRIMARY KEY,
            model_name VARCHAR(100) NOT NULL,
            model_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            horizon INTEGER,
            version VARCHAR(100) NOT NULL,
            artifact_path TEXT NOT NULL,
            feature_set_version VARCHAR(100),
            training_start_date DATE,
            training_end_date DATE,
            metrics JSONB,
            params JSONB,
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (model_name, version)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS model_training_runs (
            id BIGSERIAL PRIMARY KEY,
            run_name VARCHAR(150) NOT NULL,
            model_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            horizon INTEGER,
            train_start_date DATE,
            train_end_date DATE,
            validation_start_date DATE,
            validation_end_date DATE,
            test_start_date DATE,
            test_end_date DATE,
            dataset_snapshot TEXT,
            feature_store_version VARCHAR(100),
            status VARCHAR(30) DEFAULT 'RUNNING',
            metrics JSONB,
            params JSONB,
            notes TEXT,
            started_at TIMESTAMP DEFAULT NOW(),
            finished_at TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS forecast_model_components (
            id BIGSERIAL PRIMARY KEY,
            forecast_id INTEGER NOT NULL REFERENCES analytics_forecast(id) ON DELETE CASCADE,
            model_name VARCHAR(100) NOT NULL,
            model_type VARCHAR(50) NOT NULL,
            model_version VARCHAR(100),
            prediction NUMERIC(12,2),
            p10 NUMERIC(12,2),
            p50 NUMERIC(12,2),
            p90 NUMERIC(12,2),
            model_weight NUMERIC(8,6),
            model_confidence NUMERIC(8,6),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS forecast_backtest_results (
            id BIGSERIAL PRIMARY KEY,
            model_run_id BIGINT REFERENCES model_training_runs(id),
            model_name VARCHAR(100) NOT NULL,
            model_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            horizon INTEGER,
            commodity_id INTEGER REFERENCES dim_commodity(id),
            region_id INTEGER REFERENCES dim_region(id),
            test_start_date DATE,
            test_end_date DATE,
            mae NUMERIC(14,4),
            rmse NUMERIC(14,4),
            mape NUMERIC(12,6),
            smape NUMERIC(12,6),
            wape NUMERIC(12,6),
            r2 NUMERIC(12,6),
            coverage_p10_p90 NUMERIC(12,6),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Wire FK on analytics_forecast.model_run_id (added above as plain BIGINT).
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE analytics_forecast
            ADD CONSTRAINT fk_analytics_forecast_model_run
            FOREIGN KEY (model_run_id) REFERENCES model_training_runs(id);
        EXCEPTION WHEN duplicate_object THEN NULL;
                  WHEN undefined_column THEN NULL; END $$;
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_model_registry_active "
               "ON model_registry (model_type, target_type, horizon, is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_model_training_runs_status "
               "ON model_training_runs (status, started_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_forecast_components_forecast_id "
               "ON forecast_model_components (forecast_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_backtest_model_horizon "
               "ON forecast_backtest_results (model_name, horizon)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_forecast_target_date "
               "ON analytics_forecast (target_date)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_analytics_forecast_target_date")
    op.execute("DROP INDEX IF EXISTS idx_backtest_model_horizon")
    op.execute("DROP INDEX IF EXISTS idx_forecast_components_forecast_id")
    op.execute("DROP INDEX IF EXISTS idx_model_training_runs_status")
    op.execute("DROP INDEX IF EXISTS idx_model_registry_active")

    op.execute("ALTER TABLE analytics_forecast DROP CONSTRAINT IF EXISTS fk_analytics_forecast_model_run")
    op.execute("DROP TABLE IF EXISTS forecast_backtest_results")
    op.execute("DROP TABLE IF EXISTS forecast_model_components")
    op.execute("DROP TABLE IF EXISTS model_training_runs")
    op.execute("DROP TABLE IF EXISTS model_registry")

    for name, _ in reversed(_FORECAST_NEW_COLS):
        op.execute(f"ALTER TABLE analytics_forecast DROP COLUMN IF EXISTS {name}")
