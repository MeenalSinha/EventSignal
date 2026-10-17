"""Alembic migration environment.

Reads the database URL from the application's Settings (same source as the
application itself) so the migration and the app always target the same database.

To run migrations:
    cd backend
    .venv/Scripts/alembic upgrade head         (Windows)
    .venv/bin/alembic upgrade head             (macOS / Linux)
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

# Ensure the backend package is importable when alembic is invoked from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.models import Base

# Alembic config object.
config = context.config

# Standard Python logging configuration from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use application settings as the authoritative database URL source.
_settings = get_settings()
# Escape '%' so configparser does not fail on URL percent-encoded characters in paths
config.set_main_option("sqlalchemy.url", _settings.resolved_database_url.replace("%", "%%"))

# Provide metadata for autogenerate support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without connecting)."""
    url = _settings.resolved_database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE emulation.
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to the database directly)."""
    from app.database import create_db_engine, ensure_sqlite_directory

    ensure_sqlite_directory(_settings)
    connectable = create_db_engine(_settings.resolved_database_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE emulation.
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
