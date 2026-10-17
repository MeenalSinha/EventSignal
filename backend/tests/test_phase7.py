"""Phase 7 backend tests: Gap-to-Helper Matching & EventSignal Legacy.

Tests cover:
  - StudentNeed CRUD lifecycle
  - Matching engine (unit tests of _compute_match and run_matching_for_need)
  - HelperMatch status transitions
  - LegacyHandover lifecycle (create, update, submit, acknowledge, supersede)
  - EventMemory CRUD
  - FollowUpTask lifecycle and completion enforcement
  - API endpoint integration tests
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.campus_position import CampusPositionDefinition
from app.models.help_offer import HelpOffer, HelpOfferStatus
from app.models.helper_match import HelperMatch, MatchStatus
from app.models.institution import Institution
from app.models.legacy_handover import HandoverStatus, LegacyHandover
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.student_need import NeedStatus, NeedUrgency, StudentNeed
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.services.legacy import (
    acknowledge_handover,
    create_handover,
    submit_handover,
    update_handover,
)
from app.services.matching import SCORER_VERSION, _compute_match, run_matching_for_need


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def inst(db: Session) -> Institution:
    inst = Institution(name="Test College", slug="test-college-p7")
    db.add(inst)
    db.commit()
    return inst


@pytest.fixture()
def campus_pos(db: Session, inst: Institution) -> CampusPositionDefinition:
    pos = CampusPositionDefinition(
        institution_id=inst.id,
        title="GDSC Lead",
    )
    db.add(pos)
    db.commit()
    return pos


@pytest.fixture()
def user_a(db: Session) -> User:
    u = User(
        email="alice-p7@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Alice P7",
        is_active=True,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def user_b(db: Session) -> User:
    u = User(
        email="bob-p7@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Bob P7",
        is_active=True,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def membership_a(db: Session, inst: Institution, user_a: User) -> InstitutionMembership:
    m = InstitutionMembership(
        institution_id=inst.id,
        user_id=user_a.id,
        role=InstitutionRole.MEMBER,
        status=MembershipStatus.ACTIVE,
    )
    db.add(m)
    db.commit()
    return m


@pytest.fixture()
def membership_b(db: Session, inst: Institution, user_b: User) -> InstitutionMembership:
    m = InstitutionMembership(
        institution_id=inst.id,
        user_id=user_b.id,
        role=InstitutionRole.MEMBER,
        status=MembershipStatus.ACTIVE,
    )
    db.add(m)
    db.commit()
    return m


@pytest.fixture()
def student_profile_a(
    db: Session, inst: Institution, user_a: User, membership_a: InstitutionMembership
) -> StudentProfile:
    sp = StudentProfile(
        user_id=user_a.id,
        institution_id=inst.id,
        membership_id=membership_a.id,
        display_name="Alice Student",
    )
    db.add(sp)
    db.commit()
    return sp


@pytest.fixture()
def active_offer(db: Session, inst: Institution, user_b: User) -> HelpOffer:
    offer = HelpOffer(
        user_id=user_b.id,
        institution_id=inst.id,
        title="Mock Interview Help",
        category="mock_interview",
        description="I offer mock interviews for placement prep.",
        applicable_skills="python algorithms data-structures interview coding",
        delivery_mode="remote",
        status=HelpOfferStatus.ACTIVE,
        willing_to_help=True,
    )
    db.add(offer)
    db.commit()
    return offer


@pytest.fixture()
def open_need(
    db: Session, inst: Institution, student_profile_a: StudentProfile
) -> StudentNeed:
    need = StudentNeed(
        student_profile_id=student_profile_a.id,
        institution_id=inst.id,
        title="Need mock interview practice",
        category="mock_interview",
        description="I need help with python coding interview practice and algorithms",
        preferred_delivery_mode="remote",
        urgency=NeedUrgency.HIGH,
        status=NeedStatus.OPEN,
    )
    db.add(need)
    db.commit()
    return need


# ---------------------------------------------------------------------------
# Unit tests: matching engine
# ---------------------------------------------------------------------------


class TestComputeMatch:
    def test_perfect_category_match_scores_above_threshold(
        self, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        result = _compute_match(open_need, active_offer)
        assert result is not None
        assert result["score"] > 0.45  # category (0.45) + urgency (0.10) + some keyword overlap

    def test_category_mismatch_with_no_overlap_is_none(
        self,
        open_need: StudentNeed,
        active_offer: HelpOffer,
    ) -> None:
        # Change offer category and delivery mode so only urgency contributes
        active_offer.category = "portfolio_review"
        active_offer.applicable_skills = "design photoshop"
        active_offer.delivery_mode = "in_person"
        result = _compute_match(open_need, active_offer)
        # Score = 0 (category) + 0 (delivery) + ~0 (no overlap) + 0.10 (HIGH urgency) = 0.10
        # Exactly at threshold — should still return (threshold is 0.10)
        # But if description tokens have no overlap with "design photoshop": contribution =0
        # urgency HIGH = 0.10 ≥ threshold → returns
        assert result is not None
        assert result["score"] == pytest.approx(0.10, abs=0.01)

    def test_delivery_mode_mismatch_reduces_score(
        self,
        open_need: StudentNeed,
        active_offer: HelpOffer,
    ) -> None:
        active_offer.delivery_mode = "in_person"
        result = _compute_match(open_need, active_offer)
        assert result is not None
        # delivery mode rule should show matched=False
        delivery_rule = next(r for r in result["rule_results"] if r["rule"] == "delivery_mode_alignment")
        assert delivery_rule["matched"] is False
        assert delivery_rule["contribution"] == 0.0

    def test_no_preferred_delivery_mode_adds_uncertainty(
        self,
        open_need: StudentNeed,
        active_offer: HelpOffer,
    ) -> None:
        open_need.preferred_delivery_mode = None
        result = _compute_match(open_need, active_offer)
        assert result is not None
        assert result["uncertainty_notes"] is not None
        assert "delivery mode" in result["uncertainty_notes"].lower()

    def test_rule_results_are_complete(
        self, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        result = _compute_match(open_need, active_offer)
        assert result is not None
        rules = {r["rule"] for r in result["rule_results"]}
        assert rules == {"category_alignment", "delivery_mode_alignment", "skill_keyword_overlap", "urgency_boost"}

    def test_summary_explanation_is_set(
        self, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        result = _compute_match(open_need, active_offer)
        assert result is not None
        assert result["summary_explanation"] is not None
        assert SCORER_VERSION in result["summary_explanation"]

    def test_score_capped_at_one(
        self, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        result = _compute_match(open_need, active_offer)
        assert result is not None
        assert result["score"] <= 1.0


class TestRunMatchingForNeed:
    def test_matching_persists_matches(
        self, db: Session, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        matches = run_matching_for_need(db, open_need)
        assert len(matches) >= 1
        assert all(isinstance(m, HelperMatch) for m in matches)
        assert all(m.need_id == open_need.id for m in matches)

    def test_need_status_becomes_matched(
        self, db: Session, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        run_matching_for_need(db, open_need)
        assert open_need.status == NeedStatus.MATCHED

    def test_only_active_offers_are_matched(
        self, db: Session, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        active_offer.status = HelpOfferStatus.PAUSED
        db.commit()
        try:
            matches = run_matching_for_need(db, open_need)
            assert len(matches) == 0
            # Need stays OPEN if no matches
            assert open_need.status == NeedStatus.OPEN
        finally:
            active_offer.status = HelpOfferStatus.ACTIVE
            db.commit()

    def test_matching_non_open_need_raises(
        self, db: Session, open_need: StudentNeed
    ) -> None:
        open_need.status = NeedStatus.RESOLVED
        with pytest.raises(ValueError, match="OPEN"):
            run_matching_for_need(db, open_need)

    def test_replace_existing_expires_prior_matches(
        self, db: Session, open_need: StudentNeed, active_offer: HelpOffer
    ) -> None:
        first_batch = run_matching_for_need(db, open_need)
        assert len(first_batch) >= 1
        # Reset need status to OPEN for re-run
        open_need.status = NeedStatus.OPEN
        second_batch = run_matching_for_need(db, open_need, replace_existing=True)
        for m in first_batch:
            db.refresh(m)
            assert m.status == MatchStatus.EXPIRED
        assert len(second_batch) >= 1


# ---------------------------------------------------------------------------
# Unit tests: legacy handover service
# ---------------------------------------------------------------------------


class TestLegacyHandoverService:
    def test_create_handover_sets_draft_status(
        self, db: Session, inst: Institution, user_a: User, membership_a: InstitutionMembership
    ) -> None:
        h = create_handover(
            db,
            institution_id=inst.id,
            outgoing_user_id=user_a.id,
            title="My Tenure Handover",
        )
        assert h.status == HandoverStatus.DRAFT
        assert h.version == 1

    def test_version_increments_for_same_position(
        self,
        db: Session,
        inst: Institution,
        campus_pos: CampusPositionDefinition,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        h1 = create_handover(db, institution_id=inst.id, outgoing_user_id=user_a.id, title="H1", position_id=campus_pos.id)
        h2 = create_handover(db, institution_id=inst.id, outgoing_user_id=user_a.id, title="H2", position_id=campus_pos.id)
        assert h2.version == h1.version + 1

    def test_update_draft_by_owner_succeeds(
        self, db: Session, inst: Institution, user_a: User, membership_a: InstitutionMembership
    ) -> None:
        h = create_handover(db, institution_id=inst.id, outgoing_user_id=user_a.id, title="Original")
        h = update_handover(db, h, requesting_user_id=user_a.id, title="Updated")
        assert h.title == "Updated"

    def test_update_by_non_owner_raises_permission_error(
        self,
        db: Session,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        h = create_handover(db, institution_id=inst.id, outgoing_user_id=user_a.id, title="H")
        with pytest.raises(PermissionError):
            update_handover(db, h, requesting_user_id=user_b.id, title="Hack")

    def test_submit_transitions_to_submitted(
        self,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        h = create_handover(db, institution_id=inst.id, outgoing_user_id=user_a.id, title="H")
        h = submit_handover(db, h, requesting_user_id=user_a.id)
        assert h.status == HandoverStatus.SUBMITTED

    def test_acknowledge_transitions_to_acknowledged(
        self,
        db: Session,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        h = create_handover(
            db,
            institution_id=inst.id,
            outgoing_user_id=user_a.id,
            incoming_user_id=user_b.id,
            title="H",
        )
        h = submit_handover(db, h, requesting_user_id=user_a.id)
        h = acknowledge_handover(db, h, requesting_user_id=user_b.id)
        assert h.status == HandoverStatus.ACKNOWLEDGED
        assert h.acknowledged_at is not None

    def test_acknowledge_by_wrong_user_raises_permission_error(
        self,
        db: Session,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        h = create_handover(
            db,
            institution_id=inst.id,
            outgoing_user_id=user_a.id,
            incoming_user_id=user_b.id,
            title="H",
        )
        h = submit_handover(db, h, requesting_user_id=user_a.id)
        with pytest.raises(PermissionError):
            acknowledge_handover(db, h, requesting_user_id=user_a.id)

    def test_submit_supersedes_older_handovers_for_same_position(
        self,
        db: Session,
        inst: Institution,
        campus_pos: CampusPositionDefinition,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        pos_id = campus_pos.id
        h_old = create_handover(
            db,
            institution_id=inst.id,
            outgoing_user_id=user_a.id,
            title="Old",
            position_id=pos_id,
        )
        h_old = submit_handover(db, h_old, requesting_user_id=user_a.id)
        # Reset old to SUBMITTED for test
        assert h_old.status == HandoverStatus.SUBMITTED

        h_new = create_handover(
            db,
            institution_id=inst.id,
            outgoing_user_id=user_a.id,
            title="New",
            position_id=pos_id,
        )
        h_new = submit_handover(db, h_new, requesting_user_id=user_a.id)
        db.refresh(h_old)
        assert h_old.status == HandoverStatus.SUPERSEDED
        assert h_new.status == HandoverStatus.SUBMITTED


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestNeedsAPI:
    def test_create_need_requires_student_profile(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_b: User,
        membership_b: InstitutionMembership,
    ) -> None:
        """User without a student profile should get 404."""
        headers = _auth_headers(client, "bob-p7@example.com")
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/needs",
            json={"title": "Need help", "category": "mock_interview"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_create_need_succeeds_with_student_profile(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/needs",
            json={
                "title": "Mock interview prep",
                "category": "mock_interview",
                "description": "Need help with python coding interviews",
                "urgency": "high",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["status"] == "open"
        assert data["category"] == "mock_interview"

    def test_list_needs_returns_only_my_needs(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
        open_need: StudentNeed,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.get(f"/api/v1/institutions/{inst.id}/needs", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert all(n["student_profile_id"] == student_profile_a.id for n in data["items"])

    def test_run_matching_endpoint(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
        open_need: StudentNeed,
        active_offer: HelpOffer,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/needs/{open_need.id}/run-matching",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] >= 1
        match = data["items"][0]
        assert "rule_results" in match
        assert "summary_explanation" in match
        assert match["score"] > 0

    def test_update_need_status_to_resolved(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
        open_need: StudentNeed,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.patch(
            f"/api/v1/institutions/{inst.id}/needs/{open_need.id}",
            json={"status": "resolved"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    def test_invalid_status_transition_rejected(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
        open_need: StudentNeed,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.patch(
            f"/api/v1/institutions/{inst.id}/needs/{open_need.id}",
            json={"status": "matched"},  # Cannot set to matched via PATCH
            headers=headers,
        )
        assert resp.status_code == 422


class TestMatchStatusAPI:
    def _create_match(
        self,
        client: TestClient,
        inst: Institution,
        open_need: StudentNeed,
        active_offer: HelpOffer,
        auth_email: str,
    ) -> dict:
        headers = _auth_headers(client, auth_email)
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/needs/{open_need.id}/run-matching",
            headers=headers,
        )
        assert resp.status_code == 200
        return resp.json()["items"][0]

    def test_accept_match(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
        open_need: StudentNeed,
        active_offer: HelpOffer,
    ) -> None:
        match_data = self._create_match(
            client, inst, open_need, active_offer, "alice-p7@example.com"
        )
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.patch(
            f"/api/v1/institutions/{inst.id}/matches/{match_data['id']}/status",
            json={"status": "accepted"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_dismiss_match(
        self,
        client: TestClient,
        db: Session,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
        student_profile_a: StudentProfile,
        open_need: StudentNeed,
        active_offer: HelpOffer,
    ) -> None:
        match_data = self._create_match(
            client, inst, open_need, active_offer, "alice-p7@example.com"
        )
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.patch(
            f"/api/v1/institutions/{inst.id}/matches/{match_data['id']}/status",
            json={"status": "dismissed"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "dismissed"


class TestHandoverAPI:
    def test_create_and_list_handover(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/handovers",
            json={"title": "My Campus Role Handover"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        hid = resp.json()["id"]
        assert resp.json()["status"] == "draft"

        list_resp = client.get(
            f"/api/v1/institutions/{inst.id}/handovers", headers=headers
        )
        assert list_resp.status_code == 200
        ids = [h["id"] for h in list_resp.json()["items"]]
        assert hid in ids

    def test_submit_handover_lifecycle(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        headers_a = _auth_headers(client, "alice-p7@example.com")
        headers_b = _auth_headers(client, "bob-p7@example.com")

        # Create
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/handovers",
            json={"title": "Role Handover", "incoming_user_id": user_b.id},
            headers=headers_a,
        )
        assert resp.status_code == 201
        hid = resp.json()["id"]

        # Submit by outgoing
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/handovers/{hid}/submit",
            headers=headers_a,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "submitted"

        # Acknowledge by incoming
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/handovers/{hid}/acknowledge",
            headers=headers_b,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "acknowledged"
        assert resp.json()["acknowledged_at"] is not None

    def test_wrong_user_cannot_submit(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        headers_a = _auth_headers(client, "alice-p7@example.com")
        headers_b = _auth_headers(client, "bob-p7@example.com")

        resp = client.post(
            f"/api/v1/institutions/{inst.id}/handovers",
            json={"title": "Role Handover"},
            headers=headers_a,
        )
        assert resp.status_code == 201
        hid = resp.json()["id"]

        resp = client.post(
            f"/api/v1/institutions/{inst.id}/handovers/{hid}/submit",
            headers=headers_b,
        )
        assert resp.status_code == 422


class TestEventMemoryAPI:
    def test_create_and_get_memory(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/memories",
            json={
                "title": "Annual Hackathon 2025 Memory",
                "what_worked": "Strong participation from juniors",
                "what_did_not_work": "Venue was too small",
                "tags": ["hackathon", "2025"],
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        mid = resp.json()["id"]
        assert resp.json()["is_current"] is True

        get_resp = client.get(
            f"/api/v1/institutions/{inst.id}/memories/{mid}", headers=headers
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Annual Hackathon 2025 Memory"

    def test_list_memories_with_current_filter(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        headers = _auth_headers(client, "alice-p7@example.com")
        client.post(
            f"/api/v1/institutions/{inst.id}/memories",
            json={"title": "Memory 1", "tags": []},
            headers=headers,
        )
        resp = client.get(
            f"/api/v1/institutions/{inst.id}/memories?current_only=true", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(m["is_current"] for m in data["items"])


class TestFollowUpTaskAPI:
    def test_create_and_complete_task(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        headers_a = _auth_headers(client, "alice-p7@example.com")

        # Create task assigned to bob
        resp = client.post(
            f"/api/v1/institutions/{inst.id}/tasks",
            json={
                "title": "Reach out to mentor",
                "assignee_user_id": user_b.id,
            },
            headers=headers_a,
        )
        assert resp.status_code == 201, resp.text
        tid = resp.json()["id"]
        assert resp.json()["is_completed"] is False

        # Bob completes the task
        headers_b = _auth_headers(client, "bob-p7@example.com")
        resp = client.patch(
            f"/api/v1/institutions/{inst.id}/tasks/{tid}",
            json={"is_completed": True},
            headers=headers_b,
        )
        assert resp.status_code == 200
        assert resp.json()["is_completed"] is True
        assert resp.json()["completed_at"] is not None

    def test_only_assignee_can_complete_task(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        user_b: User,
        membership_a: InstitutionMembership,
        membership_b: InstitutionMembership,
    ) -> None:
        headers_a = _auth_headers(client, "alice-p7@example.com")

        resp = client.post(
            f"/api/v1/institutions/{inst.id}/tasks",
            json={"title": "Task", "assignee_user_id": user_b.id},
            headers=headers_a,
        )
        tid = resp.json()["id"]

        # Alice (creator, not assignee) tries to complete → 403
        resp = client.patch(
            f"/api/v1/institutions/{inst.id}/tasks/{tid}",
            json={"is_completed": True},
            headers=headers_a,
        )
        assert resp.status_code == 403

    def test_list_tasks_shows_mine(
        self,
        client: TestClient,
        inst: Institution,
        user_a: User,
        membership_a: InstitutionMembership,
    ) -> None:
        headers_a = _auth_headers(client, "alice-p7@example.com")
        client.post(
            f"/api/v1/institutions/{inst.id}/tasks",
            json={"title": "Self-task", "assignee_user_id": user_a.id},
            headers=headers_a,
        )
        resp = client.get(
            f"/api/v1/institutions/{inst.id}/tasks", headers=headers_a
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
