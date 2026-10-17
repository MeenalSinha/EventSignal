from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, Settings
from app.database import (
    check_connection,
    create_db_engine,
    ensure_sqlite_directory,
    init_db,
    missing_tables,
)
from app.main import create_app
from app.models import AlumniProfile, Base, HelpOffer, Opportunity, SourceReference, StudentProfile


def test_startup_creates_directory_database_and_tables(
    client: TestClient, settings: Settings
) -> None:
    path = settings.sqlite_file_path
    assert path is not None and path.exists()
    assert path.parent.name == "nested"
    tables = set(inspect(client.app.state.engine).get_table_names())  # type: ignore[attr-defined]
    assert {
        "opportunities",
        "source_references",
        "field_evidence",
        "student_profiles",
        "alumni_profiles",
        "match_explanations",
        "connection_requests",
    } <= tables


def test_tests_use_isolated_database(settings: Settings) -> None:
    path = settings.sqlite_file_path
    assert path is not None
    assert PROJECT_ROOT / "data" not in path.parents


def test_no_rows_are_seeded_at_startup(session: Session) -> None:
    assert session.scalar(select(func.count()).select_from(Opportunity)) == 0
    assert session.scalar(select(func.count()).select_from(SourceReference)) == 0
    assert session.scalar(select(func.count()).select_from(StudentProfile)) == 0
    assert session.scalar(select(func.count()).select_from(AlumniProfile)) == 0
    assert session.scalar(select(func.count()).select_from(HelpOffer)) == 0


def test_init_db_is_idempotent(client: TestClient) -> None:
    engine = client.app.state.engine  # type: ignore[attr-defined]
    init_db(engine)
    init_db(engine)
    assert missing_tables(engine) == []


def test_check_connection_succeeds_and_fails_appropriately(client: TestClient, tmp_path) -> None:  # type: ignore[no-untyped-def]
    check_connection(client.app.state.engine)  # type: ignore[attr-defined]
    bad_dir = tmp_path / "dir"
    bad_dir.mkdir()
    with pytest.raises(Exception, match="unable to open"):
        check_connection(create_db_engine(f"sqlite:///{bad_dir.as_posix()}"))


def test_missing_tables_detects_absent_schema(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = create_db_engine(f"sqlite:///{(tmp_path / 'empty.db').as_posix()}")
    absent = missing_tables(engine)
    assert "opportunities" in absent
    assert "source_references" in absent
    init_db(engine)
    assert missing_tables(engine) == []


def test_foreign_keys_are_enforced(client: TestClient) -> None:
    engine = client.app.state.engine  # type: ignore[attr-defined]
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_ensure_sqlite_directory_skips_memory_database(
    make_settings: Callable[..., Settings],
) -> None:
    ensure_sqlite_directory(make_settings(database_url="sqlite://"))  # must not raise


def test_session_dependency_closes_sessions(client: TestClient) -> None:
    from app.database import get_session

    class FakeRequest:
        app = client.app

    gen = get_session(FakeRequest())  # type: ignore[arg-type]
    sess = next(gen)
    assert isinstance(sess, Session)
    with pytest.raises(StopIteration):
        next(gen)


def test_startup_survives_unusable_database_and_health_reports_it(
    make_settings: Callable[..., Settings], tmp_path
) -> None:  # type: ignore[no-untyped-def]
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where a directory is needed", encoding="utf-8")
    broken = make_settings(database_url=f"sqlite:///{(blocker / 'x' / 'db.sqlite').as_posix()}")
    with TestClient(create_app(broken)) as c:
        resp = c.get("/api/v1/health")
        assert resp.status_code == 503
        assert resp.json()["status"] == "unhealthy"


def test_metadata_registers_expected_tables() -> None:
    expected = {
        "opportunities",
        "source_references",
        "field_evidence",
        "student_profiles",
        "alumni_profiles",
        "match_explanations",
        "connection_requests",
        "opportunity_assessments",
        "users",
        "institutions",
        "institution_memberships",
        "organizational_units",
        "campus_position_definitions",
        "campus_role_assignments",
        "audit_logs",
        "help_offers",
        # Phase 7 tables
        "student_needs",
        "helper_matches",
        "legacy_handovers",
        "event_memories",
        "follow_up_tasks",
        # Phase 8 tables
        "partner_organizations",
        "sponsorship_requests",
        "promotion_campaigns",
        "alumni_import_jobs",
    }
    assert set(Base.metadata.tables) == expected


def test_in_memory_database_works_across_connections() -> None:
    engine = create_db_engine("sqlite://")
    init_db(engine)
    assert missing_tables(engine) == []  # a second connection still sees the tables
