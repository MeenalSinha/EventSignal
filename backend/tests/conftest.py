"""Shared fixtures. Every test runs against an isolated temp database and ignores the
developer's real .env, so tests can never read or modify live data."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings, load_settings
from app.main import create_app

# Names read by Settings; cleared so the developer's shell cannot leak into tests.
SETTING_ENV_VARS = [
    "APP_NAME",
    "APP_VERSION",
    "APP_ENV",
    "LOG_LEVEL",
    "BACKEND_HOST",
    "BACKEND_PORT",
    "BACKEND_RELOAD",
    "DATABASE_URL",
    "CORS_ORIGINS",
    "INGEST_REQUEST_TIMEOUT_SECONDS",
    "INGEST_MAX_CONTENT_LENGTH_BYTES",
    "INGEST_MAX_REDIRECTS",
    "INGEST_USER_AGENT",
    "INGEST_ALLOWED_CONTENT_TYPES",
    "INGEST_ALLOWED_PORTS",
]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in SETTING_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def make_settings(tmp_path: Path) -> Callable[..., Settings]:
    def factory(**overrides: object) -> Settings:
        values: dict[str, object] = {
            "_env_file": None,
            "app_env": "test",
            "database_url": f"sqlite:///{(tmp_path / 'nested' / 'test.db').as_posix()}",
        }
        values.update(overrides)
        return load_settings(**values)

    return factory


@pytest.fixture
def settings(make_settings: Callable[..., Settings]) -> Settings:
    return make_settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # The context manager runs the real startup/shutdown lifespan.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session(client: TestClient) -> Iterator[Session]:
    session = client.app.state.session_factory()  # type: ignore[attr-defined]
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def forbid_real_database_creation() -> Iterator[None]:
    """Fail loudly if a test touches the repository's real database file."""
    from app.core.config import PROJECT_ROOT

    real_db = PROJECT_ROOT / "data" / "eventsignal.db"
    existed_before = real_db.exists()
    before = real_db.stat().st_mtime_ns if existed_before else None
    yield
    assert real_db.exists() == existed_before, "A test created or deleted the real database"
    if existed_before:
        assert real_db.stat().st_mtime_ns == before, "A test modified the real database"


def pytest_configure() -> None:
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
