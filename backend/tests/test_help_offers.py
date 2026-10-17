"""Tests for HelpOffer lifecycle, publishing, discovery, filtering, and connection requests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.membership import InstitutionRole


def register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": full_name},
    )
    assert res.status_code == 201
    return res.json()["access_token"]


def create_institution_helper(client: TestClient, token: str, slug: str = "offer-college") -> str:
    res = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"College {slug}", "slug": slug},
    )
    assert res.status_code == 201
    return res.json()["id"]


def join_institution_helper(client: TestClient, token: str, inst_id: str, role: str) -> None:
    res = client.post(
        f"/api/v1/institutions/{inst_id}/join",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": role},
    )
    assert res.status_code == 201


def test_help_offer_publishing_and_discovery(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin_offer@college.edu")
    inst_id = create_institution_helper(client, admin_token, "tech-univ")

    mentor_token = register_and_login(client, "mentor@college.edu", "Dr. Vikram Seth")
    join_institution_helper(client, mentor_token, inst_id, InstitutionRole.FACULTY.value)

    # 1. Mentor publishes a help offer
    res_offer = client.post(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={
            "title": "Machine Learning Research & Paper Guidance",
            "category": "research_guidance",
            "description": "Offering 1-on-1 guidance on arXiv preprints and ML project framing.",
            "applicable_skills": "PyTorch, Transformers, Computer Vision",
            "intended_audience": "students_only",
            "delivery_mode": "remote",
            "availability_description": "2 slots every Saturday afternoon",
            "willing_to_help": True,
        },
    )
    assert res_offer.status_code == 201
    offer_data = res_offer.json()
    offer_id = offer_data["id"]
    assert offer_data["title"] == "Machine Learning Research & Paper Guidance"
    assert offer_data["category"] == "research_guidance"
    assert offer_data["status"] == "active"
    assert offer_data["willing_to_help"] is True

    # 2. Mentor views their own offers
    res_mine = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers/mine",
        headers={"Authorization": f"Bearer {mentor_token}"},
    )
    assert res_mine.status_code == 200
    assert len(res_mine.json()) == 1
    assert res_mine.json()[0]["id"] == offer_id

    # 3. Student discovers active help offer
    student_token = register_and_login(client, "student_ml@college.edu", "Sneha Roy")
    join_institution_helper(client, student_token, inst_id, InstitutionRole.STUDENT.value)

    res_discovery = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_discovery.status_code == 200
    discovery_data = res_discovery.json()
    assert discovery_data["total"] == 1
    assert discovery_data["items"][0]["id"] == offer_id
    assert discovery_data["items"][0]["owner_name"] == "Dr. Vikram Seth"

    # 4. Filter by category
    res_cat = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers?category=research_guidance",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_cat.status_code == 200
    assert res_cat.json()["total"] == 1

    res_cat_empty = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers?category=mock_interview",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_cat_empty.status_code == 200
    assert res_cat_empty.json()["total"] == 0

    # 5. Search query matching applicable_skills
    res_search = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers?search=Transformers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1


def test_help_offer_lifecycle_pause_and_consent(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin_offer2@college.edu")
    inst_id = create_institution_helper(client, admin_token, "state-univ")

    mentor_token = register_and_login(client, "alum_offer@college.edu", "Alum Host")
    join_institution_helper(client, mentor_token, inst_id, InstitutionRole.ALUMNI.value)

    student_token = register_and_login(client, "student_view@college.edu", "Student Viewer")
    join_institution_helper(client, student_token, inst_id, InstitutionRole.STUDENT.value)

    res = client.post(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={
            "title": "Backend Engineering Mock Interviews",
            "category": "mock_interview",
            "description": "45-minute coding and systems design mock interview with feedback.",
        },
    )
    assert res.status_code == 201
    offer_id = res.json()["id"]

    # Visible initially
    res_initial = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_initial.json()["total"] == 1

    # Pause offer
    res_pause = client.patch(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"status": "paused"},
    )
    assert res_pause.status_code == 200
    assert res_pause.json()["status"] == "paused"

    # Immediately excluded from discovery
    res_paused_disc = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_paused_disc.json()["total"] == 0

    # Reactivate offer
    client.patch(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"status": "active"},
    )
    res_active_disc = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_active_disc.json()["total"] == 1

    # Withdraw consent (willing_to_help=False)
    client.patch(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"willing_to_help": False},
    )
    res_noconsent = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_noconsent.json()["total"] == 0


def test_purpose_specific_help_requests(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin_offer3@college.edu")
    inst_id = create_institution_helper(client, admin_token, "poly-univ")

    mentor_token = register_and_login(client, "senior_alum@college.edu", "Senior Alum")
    join_institution_helper(client, mentor_token, inst_id, InstitutionRole.ALUMNI.value)

    res_offer = client.post(
        f"/api/v1/institutions/{inst_id}/help-offers",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={
            "title": "Resume & Portfolio Review for Juniors",
            "category": "portfolio_review",
            "description": "Constructive feedback on student GitHub and design portfolios.",
        },
    )
    assert res_offer.status_code == 201
    offer_id = res_offer.json()["id"]

    # 1. Anti-self-request rejection
    res_self = client.post(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}/requests",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"purpose": "career_guidance", "message": "Can I help myself?"},
    )
    assert res_self.status_code == 400

    # 2. Student sends valid request
    student_token = register_and_login(client, "junior_student@college.edu", "Junior Student")
    join_institution_helper(client, student_token, inst_id, InstitutionRole.STUDENT.value)

    res_req = client.post(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}/requests",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "purpose": "skill_mentoring",
            "message": "Hi, I have put together my React portfolio and would love your review!",
        },
    )
    assert res_req.status_code == 201
    req_data = res_req.json()
    assert req_data["help_offer_id"] == offer_id
    assert req_data["purpose"] == "skill_mentoring"
    assert req_data["status"] == "pending"

    # 3. Duplicate pending request rejected
    res_dup = client.post(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}/requests",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"purpose": "skill_mentoring", "message": "Duplicate attempt"},
    )
    assert res_dup.status_code == 409

    # 4. Mentor views incoming requests on their offer
    res_list = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}/requests",
        headers={"Authorization": f"Bearer {mentor_token}"},
    )
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["help_offer_id"] == offer_id

    # 5. Unauthorized student cannot view requests on mentor's offer
    res_unauth = client.get(
        f"/api/v1/institutions/{inst_id}/help-offers/{offer_id}/requests",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_unauth.status_code == 403
