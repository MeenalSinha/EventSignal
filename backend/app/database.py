"""Database engine, session management, initialisation and health checks.

Engines and session factories are created once per application instance (in the
FastAPI lifespan) and stored on ``app.state``; API handlers obtain sessions only
through the ``get_session`` dependency.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.models import Base

logger = logging.getLogger(__name__)


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the given URL."""
    url = make_url(database_url)
    is_sqlite = url.get_backend_name() == "sqlite"
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
        if url.database in {None, "", ":memory:"}:
            # An in-memory database only exists per connection; share a single one.
            kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ensure_sqlite_directory(settings: Settings) -> None:
    """Create the directory that holds the SQLite file, if one is configured."""
    path: Path | None = settings.sqlite_file_path
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)


def init_db(engine: Engine) -> None:
    """Create ORM tables for a fresh database.

    Used during development and for per-test in-memory databases. For any
    persistent database where schema changes may affect existing data, run
    Alembic migrations instead (``alembic upgrade head`` from backend/).

    Never inserts any rows.
    """
    Base.metadata.create_all(bind=engine)


def check_connection(engine: Engine) -> None:
    """Raise if the database cannot execute a trivial query."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def missing_tables(engine: Engine) -> list[str]:
    """Names of expected tables that do not exist in the connected database."""
    existing = set(inspect(engine).get_table_names())
    return sorted(set(Base.metadata.tables) - existing)


def get_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency yielding a session that is always closed."""
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
