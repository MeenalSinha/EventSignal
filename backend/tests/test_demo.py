"""Comprehensive tests for Demo Mode provisioning, authentication, tenant isolation,
seeding idempotency, reset capabilities, and demonstration metrics disclaimers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import verify_password
from app.main import create_app
from app.models import (
    HelpOffer,
    Institution,
    InstitutionMembership,
    Opportunity,
    User,
)
from app.services.auth import create_user_token
from app.services.demo_service import (
    DEMO_INSTITUTION_ID,
    DemoService,
)


@pytest.fixture
def demo_settings(make_settings: Callable[..., Settings]) -> Settings:
    return make_settings(
        demo_mode_enabled=True,
        demo_user_email="demo@eventsignal.local",
        demo_user_password="DemoPassword123!",
    )


@pytest.fixture
def demo_client(demo_settings: Settings) -> TestClient:
    app = create_app(demo_settings)
    with TestClient(app) as client:
        yield client


def test_demo_account_provisioning(demo_settings: Settings) -> None:
    """Demo account is provisioned with hashed password, non-admin role, and is_demo marker."""
    app = create_app(demo_settings)
    with TestClient(app) as client:
        # App lifespan triggers provisioning
        session_factory = app.state.session_factory
        with session_factory() as session:
            user = session.query(User).filter_by(email="demo@eventsignal.local").first()
            assert user is not None
            assert user.full_name == "Alex Vance (Demo Presenter)"
            assert user.is_superuser is False
            assert user.extra_data.get("is_demo") is True
            assert verify_password("DemoPassword123!", user.hashed_password) is True

            # Verify idempotency of provisioning
            provisioned_again = DemoService.provision_demo_account(session, demo_settings)
            assert provisioned_again.id == user.id


def test_demo_login_success(demo_client: TestClient) -> None:
    """Presenter logs in with dedicated demo credentials and receives demo-authorized session."""
    response = demo_client.post(
        "/api/v1/auth/login",
        json={"email": "demo@eventsignal.local", "password": "DemoPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"

    # Validate /auth/me returns is_demo
    token = data["access_token"]
    me_resp = demo_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user"]["email"] == "demo@eventsignal.local"
    assert me_data["user"]["is_demo"] is True
    assert me_data["is_demo"] is True
    assert len(me_data["memberships"]) >= 1
    assert me_data["memberships"][0]["institution_id"] == DEMO_INSTITUTION_ID


def test_demo_login_invalid_credentials(demo_client: TestClient) -> None:
    """Invalid demo password fails with 401 Unauthorized without creating session."""
    response = demo_client.post(
        "/api/v1/auth/login",
        json={"email": "demo@eventsignal.local", "password": "IncorrectPassword!"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_demo_login_rejected_when_demo_disabled(make_settings: Callable[..., Settings]) -> None:
    """When DEMO_MODE_ENABLED=False, demo account login fails safely with 403 Forbidden."""
    disabled_settings = make_settings(
        demo_mode_enabled=False,
        demo_user_email="demo@eventsignal.local",
        demo_user_password="DemoPassword123!",
    )
    app = create_app(disabled_settings)
    with TestClient(app) as client:
        # Pre-seed user with is_demo flag in extra_data to simulate existing demo user
        session_factory = app.state.session_factory
        from app.services.auth import register_user

        with session_factory() as session:
            u = register_user(
                session=session,
                email="demo@eventsignal.local",
                password="DemoPassword123!",
                full_name="Alex Vance (Demo Presenter)",
            )
            u.extra_data = {"is_demo": True}
            session.commit()

        # Login must fail with 403 Forbidden
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "demo@eventsignal.local", "password": "DemoPassword123!"},
        )
        assert response.status_code == 403
        assert "Demo mode is currently disabled" in response.json()["detail"]


def test_guest_isolation_from_demo_opportunities_and_institutions(demo_client: TestClient) -> None:
    """Guest/public queries do NOT expose demo opportunities or demo institution."""
    # 1. Public opportunities list excludes demo opportunities
    ops_resp = demo_client.get("/api/v1/opportunities")
    assert ops_resp.status_code == 200
    items = ops_resp.json()["items"]
    demo_items = [i for i in items if i.get("institution_id") == DEMO_INSTITUTION_ID]
    assert len(demo_items) == 0, "Public listing must not leak demo opportunities to guests"

    # 2. Public /events compatibility endpoint also excludes demo opportunities
    events_resp = demo_client.get("/api/v1/events")
    assert events_resp.status_code == 200
    items = events_resp.json()["items"]
    demo_items = [i for i in items if i.get("institution_id") == DEMO_INSTITUTION_ID]
    assert len(demo_items) == 0

    # 3. Unauthenticated institutions list excludes demo institution
    inst_resp = demo_client.get("/api/v1/institutions")
    assert inst_resp.status_code == 200
    institutions = inst_resp.json()
    demo_inst = [i for i in institutions if i["id"] == DEMO_INSTITUTION_ID]
    assert len(demo_inst) == 0, "Public institution directory must not show demo workspace"

    # 4. Explicit filter by demo institution ID returns demo opportunities
    demo_ops_resp = demo_client.get(f"/api/v1/opportunities?institution_id={DEMO_INSTITUTION_ID}")
    assert demo_ops_resp.status_code == 200
    demo_feed = demo_ops_resp.json()["items"]
    assert len(demo_feed) >= 1
    assert all(i["institution_id"] == DEMO_INSTITUTION_ID for i in demo_feed)


def test_demo_seeding_idempotent_and_reset(demo_settings: Settings) -> None:
    """Seeding demo records can be executed repeatedly without duplication; reset clears demo records."""
    app = create_app(demo_settings)
    with TestClient(app) as client:
        session_factory = app.state.session_factory
        with session_factory() as session:
            # First seed
            result1 = DemoService.seed_demo_environment(session, demo_settings)
            assert result1["status"] == "success"

            # Check counts
            opps_count_1 = session.query(Opportunity).filter_by(institution_id=DEMO_INSTITUTION_ID).count()
            offers_count_1 = session.query(HelpOffer).filter_by(institution_id=DEMO_INSTITUTION_ID).count()
            assert opps_count_1 >= 2
            assert offers_count_1 >= 2

            # Re-seed (idempotency check)
            result2 = DemoService.seed_demo_environment(session, demo_settings)
            assert result2["status"] == "success"

            opps_count_2 = session.query(Opportunity).filter_by(institution_id=DEMO_INSTITUTION_ID).count()
            offers_count_2 = session.query(HelpOffer).filter_by(institution_id=DEMO_INSTITUTION_ID).count()
            assert opps_count_2 == opps_count_1
            assert offers_count_2 == offers_count_1

            # Reset demo environment
            reset_result = DemoService.reset_demo_environment(session, demo_settings)
            assert reset_result["status"] == "success"

            # Check demo records are removed
            assert session.query(Opportunity).filter_by(institution_id=DEMO_INSTITUTION_ID).count() == 0
            assert session.query(HelpOffer).filter_by(institution_id=DEMO_INSTITUTION_ID).count() == 0
            assert session.query(Institution).filter_by(id=DEMO_INSTITUTION_ID).first() is None


def test_demo_pilot_metrics_warning_disclaimer(demo_client: TestClient) -> None:
    """Pilot metrics calculated for demo workspace include prominent DEMO DATA disclaimers."""
    login_resp = demo_client.post(
        "/api/v1/auth/login",
        json={"email": "demo@eventsignal.local", "password": "DemoPassword123!"},
    )
    token = login_resp.json()["access_token"]
    resp = demo_client.get(
        f"/api/v1/institutions/{DEMO_INSTITUTION_ID}/pilot-metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["institution_id"] == DEMO_INSTITUTION_ID
    assert metrics["readiness_status"] == "ready_for_controlled_pilot"
    assert any("DEMO DATA / DEMONSTRATION METRICS" in note for note in metrics["notes"])


def test_demo_api_status_and_actions(demo_client: TestClient) -> None:
    """Test /auth/demo/status, /auth/demo/seed, and /auth/demo/reset endpoints."""
    # 1. Status
    status_resp = demo_client.get("/api/v1/auth/demo/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["demo_mode_enabled"] is True
    assert status_resp.json()["demo_institution_id"] == DEMO_INSTITUTION_ID

    # 2. Reset
    reset_resp = demo_client.post("/api/v1/auth/demo/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "success"

    # Status shows unseeded
    status_resp2 = demo_client.get("/api/v1/auth/demo/status")
    assert status_resp2.json()["demo_dataset_seeded"] is False

    # 3. Seed
    seed_resp = demo_client.post("/api/v1/auth/demo/seed")
    assert seed_resp.status_code == 200
    assert seed_resp.json()["status"] == "success"

    # Status shows seeded
    status_resp3 = demo_client.get("/api/v1/auth/demo/status")
    assert status_resp3.json()["demo_dataset_seeded"] is True
