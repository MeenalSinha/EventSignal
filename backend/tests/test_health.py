from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import database
from app.core.config import Settings
from app.database import create_db_engine
from app.main import API_V1_PREFIX
from app.models import Base

URL = f"{API_V1_PREFIX}/health"


def test_healthy_response_has_documented_structure(client: TestClient, settings: Settings) -> None:
    resp = client.get(URL)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {
        "status",
        "message",
        "app_name",
        "version",
        "environment",
        "checked_at",
        "components",
    }
    assert body["status"] == "healthy"
    assert body["version"] == settings.app_version
    assert body["environment"] == "test"
    assert set(body["components"]) == {"api", "database"}
    assert body["components"]["database"]["status"] == "ok"
    datetime.fromisoformat(body["checked_at"])


def test_health_actually_checks_the_database(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[object] = []
    real = database.check_connection

    def spy(engine):  # type: ignore[no-untyped-def]
        calls.append(engine)
        return real(engine)

    monkeypatch.setattr("app.api.health.check_connection", spy)
    client.get(URL)
    client.get(URL)
    assert len(calls) == 2


def test_unreachable_database_is_reported_unhealthy(client: TestClient, tmp_path: Path) -> None:
    # A directory is not a valid SQLite file, so connecting genuinely fails.
    broken_dir = tmp_path / "not-a-database"
    broken_dir.mkdir()
    client.app.state.engine = create_db_engine(f"sqlite:///{broken_dir.as_posix()}")  # type: ignore[attr-defined]

    resp = client.get(URL)
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "unhealthy"
    assert body["components"]["database"]["status"] == "unavailable"
    assert body["components"]["api"]["status"] == "ok"


def test_unreachable_database_response_leaks_nothing(client: TestClient, tmp_path: Path) -> None:
    secret_dir = tmp_path / "super-secret-location"
    secret_dir.mkdir()
    client.app.state.engine = create_db_engine(f"sqlite:///{secret_dir.as_posix()}")  # type: ignore[attr-defined]
    text = client.get(URL).text
    assert "super-secret-location" not in text
    assert str(tmp_path) not in text
    assert "Traceback" not in text
    assert "sqlite" not in text.lower()


def test_missing_tables_are_degraded_not_healthy(client: TestClient) -> None:
    engine = client.app.state.engine  # type: ignore[attr-defined]
    Base.metadata.drop_all(bind=engine)
    resp = client.get(URL)
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["components"]["database"]["status"] == "degraded"


def test_health_recovers_after_schema_restored(client: TestClient) -> None:
    engine = client.app.state.engine  # type: ignore[attr-defined]
    Base.metadata.drop_all(bind=engine)
    assert client.get(URL).status_code == 503
    database.init_db(engine)
    assert client.get(URL).status_code == 200


def test_health_does_not_modify_data(client: TestClient, session: Session) -> None:
    from sqlalchemy import func, select

    from app.models import Event

    client.get(URL)
    assert session.scalar(select(func.count()).select_from(Event)) == 0
