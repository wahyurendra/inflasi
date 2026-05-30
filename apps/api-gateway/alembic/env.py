"""Alembic migration environment (async).

Resolves the DB URL from ANALYTICS_DATABASE_URL the same way app/database.py does
(asyncpg driver), and points autogenerate at the
SQLAlchemy metadata in app/models/tables.py.
"""

import asyncio
import os

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Import Base + register all ORM tables on its metadata (side-effect import).
from app.database import Base
from app.config import settings
import app.models.tables  # noqa: F401

config = context.config
target_metadata = Base.metadata


def _resolve_url() -> tuple[str, dict]:
    raw = (
        os.getenv("ANALYTICS_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or settings.analytics_database_url
    )
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)

    connect_args: dict = {}
    return raw, connect_args


def run_migrations_offline() -> None:
    url, _ = _resolve_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    url, connect_args = _resolve_url()
    engine = create_async_engine(url, connect_args=connect_args, pool_pre_ping=True)
    async with engine.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
