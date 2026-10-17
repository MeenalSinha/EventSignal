"""Phase 8 Comprehensive Integration & Functional Test Suite.

Covers:
1. Sponsorship facilitation & partner organization tracking.
2. Cross-college promotion campaigns with transparent disclosures.
3. Approved alumni CSV batch import with zero default consent.
4. Pilot & release evaluation metrics from real persisted data.
5. Cross-institution security isolation and RBAC.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token, hash_password
from app.models.institution import Institution, InstitutionStatus, InstitutionVerificationStatus
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.opportunity import Opportunity, OpportunityType, ParticipationMode
from app.models.user import User


@pytest.fixture
def phase8_test_setup(session: Session, settings: Settings) -> dict[str, Any]:
    """Fixture providing isolated institutions, users, and opportunities for Phase 8."""
    # Institution A (Source)
    inst_a = Institution(
        name="Apex Institute of Technology",
        slug="apex-tech",
        domain="apex.edu",
        verification_status=InstitutionVerificationStatus.VERIFIED,
        status=InstitutionStatus.ACTIVE,
    )
    # Institution B (Target)
    inst_b = Institution(
        name="Beacon State University",
        slug="beacon-state",
        domain="beacon.edu",
        verification_status=InstitutionVerificationStatus.VERIFIED,
        status=InstitutionStatus.ACTIVE,
    )
    # Institution C (Unrelated)
    inst_c = Institution(
        name="Crestline College",
        slug="crestline",
        domain="crestline.edu",
        verification_status=InstitutionVerificationStatus.VERIFIED,
        status=InstitutionStatus.ACTIVE,
    )
    session.add_all([inst_a, inst_b, inst_c])
    session.flush()

    # User 1: Apex Organizer / Admin
    organizer = User(
        email="organizer@apex.edu",
        hashed_password=hash_password("Secret123!"),
        full_name="Alice Organizer",
        is_active=True,
    )
    # User 2: Apex Student
    student = User(
        email="student@apex.edu",
        hashed_password=hash_password("Secret123!"),
        full_name="Bob Student",
        is_active=True,
    )
    # User 3: Beacon Reviewer / Admin
    beacon_admin = User(
        email="admin@beacon.edu",
        hashed_password=hash_password("Secret123!"),
        full_name="Carol Reviewer",
        is_active=True,
    )
    # User 4: Crestline Outsider
    outsider = User(
        email="outsider@crestline.edu",
        hashed_password=hash_password("Secret123!"),
        full_name="Dan Outsider",
        is_active=True,
    )
    session.add_all([organizer, student, beacon_admin, outsider])
    session.flush()

    # Memberships
    mem_a_admin = InstitutionMembership(
        institution_id=inst_a.id,
        user_id=organizer.id,
        role=InstitutionRole.INSTITUTION_ADMIN,
        status=MembershipStatus.ACTIVE,
    )
    mem_a_student = InstitutionMembership(
        institution_id=inst_a.id,
        user_id=student.id,
        role=InstitutionRole.STUDENT,
        status=MembershipStatus.ACTIVE,
    )
    mem_b_admin = InstitutionMembership(
        institution_id=inst_b.id,
        user_id=beacon_admin.id,
        role=InstitutionRole.INSTITUTION_ADMIN,
        status=MembershipStatus.ACTIVE,
    )
    mem_c_student = InstitutionMembership(
        institution_id=inst_c.id,
        user_id=outsider.id,
        role=InstitutionRole.STUDENT,
        status=MembershipStatus.ACTIVE,
    )
    session.add_all([mem_a_admin, mem_a_student, mem_b_admin, mem_c_student])

    # Ingested Opportunity at Apex
    opp = Opportunity(
        institution_id=inst_a.id,
        title="Apex Annual Hackathon 2026",
        opportunity_type=OpportunityType.HACKATHON,
        mode=ParticipationMode.HYBRID,
        location="Apex Center Hall",
    )
    session.add(opp)
    session.commit()

    token_organizer = create_access_token(organizer.id, settings.auth_secret_key)
    token_student = create_access_token(student.id, settings.auth_secret_key)
    token_beacon = create_access_token(beacon_admin.id, settings.auth_secret_key)
    token_outsider = create_access_token(outsider.id, settings.auth_secret_key)

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "inst_c": inst_c,
        "organizer": organizer,
        "student": student,
        "beacon_admin": beacon_admin,
        "outsider": outsider,
        "opp": opp,
        "headers_organizer": {"Authorization": f"Bearer {token_organizer}"},
        "headers_student": {"Authorization": f"Bearer {token_student}"},
        "headers_beacon": {"Authorization": f"Bearer {token_beacon}"},
        "headers_outsider": {"Authorization": f"Bearer {token_outsider}"},
    }


# ===========================================================================
# 1. Sponsorship Facilitation Tests
# ===========================================================================


def test_sponsorship_partner_creation_and_listing(
    client: TestClient, phase8_test_setup: dict[str, Any]
) -> None:
    data = phase8_test_setup
    inst_id = data["inst_a"].id

    # Create partner
    payload = {
        "name": "CloudCorp Systems",
        "industry": "Enterprise Cloud",
        "contact_name": "Sarah Connor",
        "contact_email": "sarah@cloudcorp.com",
        "website_url": "https://cloudcorp.com",
        "verification_status": "unverified",
        "notes": "Met at campus career fair",
    }
    res = client.post(
        f"/api/v1/institutions/{inst_id}/partners",
        json=payload,
        headers=data["headers_organizer"],
    )
    assert res.status_code == 201
    partner_id = res.json()["id"]
    assert res.json()["name"] == "CloudCorp Systems"
    assert res.json()["verification_status"] == "unverified"

    # List partners
    list_res = client.get(
        f"/api/v1/institutions/{inst_id}/partners",
        headers=data["headers_organizer"],
    )
    assert list_res.status_code == 200
    assert any(p["id"] == partner_id for p in list_res.json())

    # Cross-institution isolation: Beacon cannot see Apex partners
    other_res = client.get(
        f"/api/v1/institutions/{data['inst_b'].id}/partners",
        headers=data["headers_beacon"],
    )
    assert other_res.status_code == 200
    assert not any(p["id"] == partner_id for p in other_res.json())


def test_sponsorship_request_lifecycle_and_commercial_terms(
    client: TestClient, phase8_test_setup: dict[str, Any]
) -> None:
    data = phase8_test_setup
    inst_id = data["inst_a"].id
    opp_id = data["opp"].id

    # 1. Create sponsorship draft
    payload = {
        "objective": "Title Track Sponsor for Apex Hackathon",
        "proposed_benefits": "Keynote speaking slot, booth, resume access",
        "opportunity_id": opp_id,
        "support_type": "financial",
        "budget_currency": "USD",
        "budget_amount": 5000.0,
        "contact_email": "hackathon@apex.edu",
        "commercial_terms": {
            "proposed_commission_pct": 5.0,
            "agreed_terms": None,
            "payment_status": "unconfirmed",
        },
    }
    create_res = client.post(
        f"/api/v1/institutions/{inst_id}/sponsorships",
        json=payload,
        headers=data["headers_organizer"],
    )
    assert create_res.status_code == 201
    req_id = create_res.json()["id"]
    assert create_res.json()["status"] == "draft"
    assert create_res.json()["budget_amount"] == 5000.0

    # 2. Transition: DRAFT -> SUBMITTED
    sub_res = client.patch(
        f"/api/v1/institutions/{inst_id}/sponsorships/{req_id}/status",
        json={"status": "submitted"},
        headers=data["headers_organizer"],
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "submitted"

    # 3. Transition: SUBMITTED -> UNDER_REVIEW
    rev_res = client.patch(
        f"/api/v1/institutions/{inst_id}/sponsorships/{req_id}/status",
        json={"status": "under_review"},
        headers=data["headers_organizer"],
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "under_review"

    # 4. Transition: UNDER_REVIEW -> ACCEPTED with confirmed commercial terms
    acc_res = client.patch(
        f"/api/v1/institutions/{inst_id}/sponsorships/{req_id}/status",
        json={
            "status": "accepted",
            "commercial_terms": {
                "agreed_terms": "Mutual sponsorship agreement executed offline",
                "payment_status": "manual_invoiced_pending_check",
            },
        },
        headers=data["headers_organizer"],
    )
    assert acc_res.status_code == 200
    assert acc_res.json()["status"] == "accepted"
    assert acc_res.json()["commercial_terms"]["payment_status"] == "manual_invoiced_pending_check"

    # 5. Invalid transition rejected: ACCEPTED -> DRAFT
    bad_res = client.patch(
        f"/api/v1/institutions/{inst_id}/sponsorships/{req_id}/status",
        json={"status": "draft"},
        headers=data["headers_organizer"],
    )
    assert bad_res.status_code == 400

    # 6. Unauthorized user (Outsider) blocked from Apex sponsorships
    unauth_res = client.get(
        f"/api/v1/institutions/{inst_id}/sponsorships",
        headers=data["headers_outsider"],
    )
    assert unauth_res.status_code == 403


# ===========================================================================
# 2. Cross-College Promotion Campaign Tests
# ===========================================================================


def test_cross_college_promotion_workflow_and_feed(
    client: TestClient, phase8_test_setup: dict[str, Any]
) -> None:
    data = phase8_test_setup
    source_id = data["inst_a"].id
    target_id = data["inst_b"].id
    unrelated_id = data["inst_c"].id
    opp_id = data["opp"].id

    # 1. Get pricing packages
    pkg_res = client.get("/api/v1/campaigns/pricing-packages")
    assert pkg_res.status_code == 200
    assert len(pkg_res.json()) >= 3

    # 2. Create campaign targeting Beacon State
    now = datetime.now(UTC)
    payload = {
        "opportunity_id": opp_id,
        "target_institution_ids": [target_id],
        "campaign_type": "featured_spotlight",
        "pricing_package": "standard_cross_college",
        "start_date": (now - timedelta(days=1)).isoformat(),
        "end_date": (now + timedelta(days=6)).isoformat(),
    }
    camp_res = client.post(
        f"/api/v1/institutions/{source_id}/campaigns",
        json=payload,
        headers=data["headers_organizer"],
    )
    assert camp_res.status_code == 201
    camp_id = camp_res.json()["id"]
    assert camp_res.json()["status"] == "draft"
    assert camp_res.json()["is_paid_placement"] is True
    assert camp_res.json()["sponsored_label"] == "Featured — Sponsored"

    # 3. Before review: target institution's feed is empty
    feed_before = client.get(
        f"/api/v1/institutions/{target_id}/campaigns/feed",
        headers=data["headers_beacon"],
    )
    assert feed_before.status_code == 200
    assert not any(item["campaign_id"] == camp_id for item in feed_before.json())

    # 4. Review and approve campaign by Admin
    rev_res = client.post(
        f"/api/v1/institutions/{source_id}/campaigns/{camp_id}/review",
        json={"action": "approve", "review_notes": "Meets institutional promotion guidelines"},
        headers=data["headers_organizer"],
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] in ("approved", "active")

    # 5. After approval: Beacon State sees the sponsored item with prominent label
    feed_after = client.get(
        f"/api/v1/institutions/{target_id}/campaigns/feed",
        headers=data["headers_beacon"],
    )
    assert feed_after.status_code == 200
    matched = [item for item in feed_after.json() if item["campaign_id"] == camp_id]
    assert len(matched) == 1
    assert matched[0]["sponsored_label"] == "Featured — Sponsored"
    assert matched[0]["is_paid_placement"] is True
    assert matched[0]["opportunity_title"] == "Apex Annual Hackathon 2026"

    # 6. Unrelated institution (Crestline) does NOT see this campaign
    unrelated_feed = client.get(
        f"/api/v1/institutions/{unrelated_id}/campaigns/feed",
        headers=data["headers_outsider"],
    )
    assert unrelated_feed.status_code == 200
    assert not any(item["campaign_id"] == camp_id for item in unrelated_feed.json())


# ===========================================================================
# 3. Approved Alumni CSV Import Tests
# ===========================================================================


def test_alumni_csv_import_preview_and_commit(
    client: TestClient, phase8_test_setup: dict[str, Any], session: Session
) -> None:
    data = phase8_test_setup
    inst_id = data["inst_a"].id

    csv_data = (
        "email,full_name,grad_year,degree,current_role,company\n"
        "alumni1@apex.edu,Grace Hopper,2018,B.S. CS,Systems Engineer,Naval Research\n"
        "alumni2@apex.edu,Claude Shannon,2015,Ph.D. EE,Research Scientist,Bell Labs\n"
        "alumni1@apex.edu,Duplicate Grace,2018,B.S. CS,Systems Engineer,Naval Research\n"
        "bad-row-no-email,,2020,B.A.,Student,None\n"
    )

    # 1. Preview dry-run
    preview_res = client.post(
        f"/api/v1/institutions/{inst_id}/alumni-import/preview",
        json={"filename": "alumni_class_list.csv", "csv_text": csv_data},
        headers=data["headers_organizer"],
    )
    assert preview_res.status_code == 200
    preview = preview_res.json()
    assert preview["total_rows"] == 4
    assert preview["valid_rows"] == 2
    assert preview["duplicate_rows"] == 1
    assert preview["invalid_rows"] == 1
    assert "pending consent" in preview["consent_notice"]

    # 2. Non-admin student cannot commit import
    unauth_commit = client.post(
        f"/api/v1/institutions/{inst_id}/alumni-import/commit",
        json={"filename": "alumni_class_list.csv", "csv_text": csv_data},
        headers=data["headers_student"],
    )
    assert unauth_commit.status_code == 403

    # 3. Commit import as Admin
    commit_res = client.post(
        f"/api/v1/institutions/{inst_id}/alumni-import/commit",
        json={"filename": "alumni_class_list.csv", "csv_text": csv_data},
        headers=data["headers_organizer"],
    )
    assert commit_res.status_code == 201
    job = commit_res.json()
    assert job["accepted_rows"] == 2
    assert job["skipped_rows"] == 1
    assert job["rejected_rows"] == 1
    assert job["status"] == "committed"

    # 4. CRITICAL PRIVACY VERIFICATION: verify imported user profile has willing_to_connect=False
    from app.models.alumni_profile import AlumniProfile

    imported_user = session.scalar(select(User).where(User.email == "alumni1@apex.edu"))
    assert imported_user is not None
    prof = session.scalar(
        select(AlumniProfile).where(
            AlumniProfile.institution_id == inst_id,
            AlumniProfile.user_id == imported_user.id,
        )
    )
    assert prof is not None
    assert prof.willing_to_connect is False  # Zero-consent guarantee
    assert prof.visibility.value == "private"  # Private by default


# ===========================================================================
# 4. Pilot & Release Evaluation Metrics Tests
# ===========================================================================


def test_pilot_metrics_calculation(client: TestClient, phase8_test_setup: dict[str, Any]) -> None:
    data = phase8_test_setup
    inst_id = data["inst_a"].id

    res = client.get(
        f"/api/v1/institutions/{inst_id}/pilot-metrics",
        headers=data["headers_organizer"],
    )
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["institution_id"] == inst_id
    assert metrics["readiness_status"] == "ready_for_controlled_pilot"
    assert "opportunities" in metrics
    assert "student_needs" in metrics
    assert "helper_matches" in metrics
    assert "legacy_knowledge" in metrics
    assert "sponsorship" in metrics
    assert "cross_college_promotion" in metrics
    assert "alumni_network" in metrics
    assert len(metrics["notes"]) >= 3
