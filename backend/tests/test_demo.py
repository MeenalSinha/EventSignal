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
    AlumniProfile,
    CampusPositionDefinition,
    CampusRoleAssignment,
    EventMemory,
    FieldEvidence,
    FollowUpTask,
    HelperMatch,
    HelpOffer,
    Institution,
    InstitutionMembership,
    LegacyHandover,
    Opportunity,
    OpportunityAssessment,
    OrganizationalUnit,
    PartnerOrganization,
    PromotionCampaign,
    SourceReference,
    SponsorshipRequest,
    StudentNeed,
    StudentProfile,
    User,
)
from app.services.auth import create_user_token
from app.services.demo_service import (
    ALL_DEMO_OPPORTUNITY_IDS,
    ALL_DEMO_USER_IDS,
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


def test_demo_interconnected_campus_community(demo_settings: Settings) -> None:
    """Verifies that all 30 demo users, academic units, positions, and profiles are properly interconnected."""
    app = create_app(demo_settings)
    with TestClient(app) as client:
        session_factory = app.state.session_factory
        with session_factory() as session:
            # 1. 30 Demo Users provisioned with is_demo marker
            users = session.query(User).filter(User.id.in_(ALL_DEMO_USER_IDS)).all()
            assert len(users) == 30
            for u in users:
                assert u.extra_data.get("is_demo") is True
                assert u.is_superuser is False

            # 2. Institution memberships
            memberships = session.query(InstitutionMembership).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(memberships) >= 30

            # 3. Academic units & student clubs (5 depts + 8 clubs/societies)
            units = session.query(OrganizationalUnit).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(units) == 13
            clubs = [u for u in units if u.unit_type in ("club", "society", "committee")]
            assert len(clubs) == 8
            # Verify clubs have parent department relationships
            assert all(c.parent_id is not None for c in clubs)

            # 4. Verified campus leadership positions
            positions = session.query(CampusPositionDefinition).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(positions) == 10
            assignments = session.query(CampusRoleAssignment).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(assignments) >= 10
            assert all(a.verification_status.value == "verified" for a in assignments)

            # 5. Student profiles with year, major, skills, and goals
            student_profiles = session.query(StudentProfile).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(student_profiles) >= 19
            for sp in student_profiles:
                assert sp.extra_data.get("graduation_year") >= 2000
                assert sp.skills is not None and len(sp.skills) > 0
                assert sp.visibility.value == "public"

            # 6. Alumni mentor profiles with graduation year and employer
            alumni_profiles = session.query(AlumniProfile).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(alumni_profiles) >= 7
            for ap in alumni_profiles:
                assert ap.years_experience >= 1
                assert ap.willing_to_connect is True
                assert ap.professional_domain is not None
                assert ap.extra_data.get("graduation_year") >= 2017


def test_demo_opportunities_evidence_and_help_offers(demo_settings: Settings) -> None:
    """Verifies 12 opportunities, field evidence, completeness assessments, and 12 help offers."""
    app = create_app(demo_settings)
    with TestClient(app) as client:
        session_factory = app.state.session_factory
        with session_factory() as session:
            # 1. 12 Opportunities linked to demo institution
            opps = session.query(Opportunity).filter(Opportunity.id.in_(ALL_DEMO_OPPORTUNITY_IDS)).all()
            assert len(opps) == 12

            # 2. Source references and field evidence
            sources = session.query(SourceReference).all()
            assert len(sources) >= 12
            evidence = session.query(FieldEvidence).all()
            assert len(evidence) >= 12

            # 3. Completeness assessments
            assessments = session.query(OpportunityAssessment).all()
            assert len(assessments) >= 12
            assert all(0.0 <= a.overall_score <= 1.0 for a in assessments)

            # 4. 12 Connected Help Offers
            offers = session.query(HelpOffer).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(offers) == 12
            assert all(o.status == "active" and o.willing_to_help is True for o in offers)
            assert all(o.delivery_mode in ("remote", "in_person", "async", "hybrid") for o in offers)


def test_demo_matching_engine_and_legacy_records(demo_settings: Settings) -> None:
    """Verifies student needs, algorithmic matches, legacy handovers, memories, and tasks."""
    app = create_app(demo_settings)
    with TestClient(app) as client:
        session_factory = app.state.session_factory
        with session_factory() as session:
            # 1. Student needs and rule-derived matches
            needs = session.query(StudentNeed).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(needs) == 4
            matches = session.query(HelperMatch).all()
            assert len(matches) >= 3
            # Matches must have score and summary_explanation
            for m in matches:
                assert m.score > 0.0
                assert m.summary_explanation is not None and len(m.summary_explanation) > 0

            # 2. Legacy handovers
            handovers = session.query(LegacyHandover).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(handovers) == 3

            # 3. Event memories
            memories = session.query(EventMemory).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(memories) == 3

            # 4. Follow-up tasks
            tasks = session.query(FollowUpTask).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(tasks) == 6


def test_demo_partnerships_and_promotions(demo_settings: Settings) -> None:
    """Verifies partners, sponsorships, and cross-college paid promotion records."""
    app = create_app(demo_settings)
    with TestClient(app) as client:
        session_factory = app.state.session_factory
        with session_factory() as session:
            # 1. Partner organizations
            partners = session.query(PartnerOrganization).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(partners) == 3

            # 2. Sponsorship requests
            sponsorships = session.query(SponsorshipRequest).filter_by(institution_id=DEMO_INSTITUTION_ID).all()
            assert len(sponsorships) == 3

            # 3. Promotion campaigns
            campaigns = session.query(PromotionCampaign).filter_by(source_institution_id=DEMO_INSTITUTION_ID).all()
            assert len(campaigns) == 2
            assert all(c.is_paid_placement is True for c in campaigns)

