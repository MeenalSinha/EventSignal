"""Tests for StudentProfile, AlumniProfile, and Member Discovery in Phase 6."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.alumni_profile import ProfileVisibility as AlumniVisibility
from app.models.membership import InstitutionRole
from app.models.student_profile import ProfileVisibility as StudentVisibility


def register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> str:
    """Helper to register and return a bearer token."""
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": full_name},
    )
    assert res.status_code == 201
    return res.json()["access_token"]


def create_institution_helper(client: TestClient, token: str, slug: str = "test-college") -> str:
    """Helper to create an institution workspace and return its ID."""
    res = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"Test College {slug}", "slug": slug},
    )
    assert res.status_code == 201
    return res.json()["id"]


def join_institution_helper(client: TestClient, token: str, inst_id: str, role: str) -> None:
    """Helper to join an institution with a specific role."""
    res = client.post(
        f"/api/v1/institutions/{inst_id}/join",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": role},
    )
    assert res.status_code == 201


def test_student_profile_lifecycle(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin_life@example.com", "Admin Creator")
    inst_id = create_institution_helper(client, admin_token, "univ-a")

    student_token = register_and_login(client, "student1@example.com", "Aarav Sharma")
    join_institution_helper(client, student_token, inst_id, InstitutionRole.STUDENT.value)

    # 1. 404 before creation
    res = client.get(
        f"/api/v1/institutions/{inst_id}/profiles/student/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 404

    # 2. Create student profile
    res = client.post(
        f"/api/v1/institutions/{inst_id}/profiles/student",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "display_name": "Aarav S.",
            "skills": "Python, Machine Learning, PyTorch",
            "interests": "Generative AI, Autonomous Systems",
            "career_goals": "ML Research Engineer",
            "preferred_opportunity_types": "internship, research",
            "visibility": StudentVisibility.PUBLIC.value,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["display_name"] == "Aarav S."
    assert "Python" in data["skills"]
    assert data["visibility"] == StudentVisibility.PUBLIC.value

    # 3. Duplicate creation rejected
    res_dup = client.post(
        f"/api/v1/institutions/{inst_id}/profiles/student",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"display_name": "Duplicate"},
    )
    assert res_dup.status_code == 409

    # 4. Read profile
    res_get = client.get(
        f"/api/v1/institutions/{inst_id}/profiles/student/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["career_goals"] == "ML Research Engineer"

    # 5. Incremental update
    res_patch = client.patch(
        f"/api/v1/institutions/{inst_id}/profiles/student",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"career_goals": "AI Startup Founder", "visibility": StudentVisibility.PRIVATE.value},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["career_goals"] == "AI Startup Founder"
    assert res_patch.json()["visibility"] == StudentVisibility.PRIVATE.value


def test_alumni_profile_lifecycle_and_role_gate(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin_b@example.com")
    inst_id = create_institution_helper(client, admin_token, "univ-b")

    student_token = register_and_login(client, "student_only@example.com")
    join_institution_helper(client, student_token, inst_id, InstitutionRole.STUDENT.value)

    # Student cannot create alumni profile
    res_invalid = client.post(
        f"/api/v1/institutions/{inst_id}/profiles/alumni",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"display_name": "Fake Alum"},
    )
    assert res_invalid.status_code == 403

    # Alumnus joins and creates profile
    alum_token = register_and_login(client, "alumnus@example.com", "Rohan Mehta")
    join_institution_helper(client, alum_token, inst_id, InstitutionRole.ALUMNI.value)

    res_create = client.post(
        f"/api/v1/institutions/{inst_id}/profiles/alumni",
        headers={"Authorization": f"Bearer {alum_token}"},
        json={
            "display_name": "Rohan M.",
            "professional_domain": "Fintech / Cloud Infrastructure",
            "skills": "Go, Kubernetes, Distributed Systems",
            "industry": "Financial Technology",
            "years_experience": 6,
            "mentoring_interests": "Mock interviews, career transitions",
            "willing_to_connect": True,
            "monthly_connection_limit": 5,
            "visibility": AlumniVisibility.STUDENTS_ONLY.value,
        },
    )
    assert res_create.status_code == 201
    alum_data = res_create.json()
    assert alum_data["willing_to_connect"] is True
    assert alum_data["monthly_connection_limit"] == 5
    assert alum_data["years_experience"] == 6

    # Update willing_to_connect consent withdrawal
    res_withdraw = client.patch(
        f"/api/v1/institutions/{inst_id}/profiles/alumni",
        headers={"Authorization": f"Bearer {alum_token}"},
        json={"willing_to_connect": False},
    )
    assert res_withdraw.status_code == 200
    assert res_withdraw.json()["willing_to_connect"] is False


def test_member_discovery_and_privacy_controls(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin_c@example.com")
    inst_id = create_institution_helper(client, admin_token, "univ-c")

    # Member 1: Student with PRIVATE profile
    token_pvt = register_and_login(client, "pvt_student@example.com", "Private Student")
    join_institution_helper(client, token_pvt, inst_id, InstitutionRole.STUDENT.value)
    client.post(
        f"/api/v1/institutions/{inst_id}/profiles/student",
        headers={"Authorization": f"Bearer {token_pvt}"},
        json={"display_name": "Secret Student", "visibility": StudentVisibility.PRIVATE.value},
    )

    # Member 2: Student with PUBLIC profile
    token_pub = register_and_login(client, "pub_student@example.com", "Public Student")
    join_institution_helper(client, token_pub, inst_id, InstitutionRole.STUDENT.value)
    client.post(
        f"/api/v1/institutions/{inst_id}/profiles/student",
        headers={"Authorization": f"Bearer {token_pub}"},
        json={
            "display_name": "Open Student",
            "skills": "React, TypeScript",
            "visibility": StudentVisibility.PUBLIC.value,
        },
    )

    # Member 3: Alum with STUDENTS_ONLY profile
    token_alum = register_and_login(client, "alum_mentor@example.com", "Mentor Alum")
    join_institution_helper(client, token_alum, inst_id, InstitutionRole.ALUMNI.value)
    client.post(
        f"/api/v1/institutions/{inst_id}/profiles/alumni",
        headers={"Authorization": f"Bearer {token_alum}"},
        json={
            "display_name": "Senior Eng",
            "skills": "Rust, Backend Architecture",
            "visibility": AlumniVisibility.STUDENTS_ONLY.value,
        },
    )

    # When student views discovery:
    res_discovery = client.get(
        f"/api/v1/institutions/{inst_id}/profiles/members",
        headers={"Authorization": f"Bearer {token_pub}"},
    )
    assert res_discovery.status_code == 200
    items = res_discovery.json()["items"]
    assert len(items) >= 3

    # Check that Private Student's student_profile is None for others
    pvt_item = next(i for i in items if i["full_name"] == "Private Student")
    assert pvt_item["student_profile"] is None

    # Check that Public Student's profile is visible
    pub_item = next(i for i in items if i["full_name"] == "Public Student")
    assert pub_item["student_profile"] is not None
    assert pub_item["student_profile"]["display_name"] == "Open Student"

    # Check that Alum's STUDENTS_ONLY profile is visible to Student
    alum_item = next(i for i in items if i["full_name"] == "Mentor Alum")
    assert alum_item["alumni_profile"] is not None
    assert alum_item["alumni_profile"]["display_name"] == "Senior Eng"

    # Search filter by skill
    res_search = client.get(
        f"/api/v1/institutions/{inst_id}/profiles/members?search=Rust",
        headers={"Authorization": f"Bearer {token_pub}"},
    )
    assert res_search.status_code == 200
    search_items = res_search.json()["items"]
    assert len(search_items) == 1
    assert search_items[0]["full_name"] == "Mentor Alum"


def test_cross_institution_isolation(client: TestClient) -> None:
    token_a = register_and_login(client, "college_a_member@example.com")
    inst_a = create_institution_helper(client, token_a, "college-alpha")

    token_b = register_and_login(client, "college_b_member@example.com")
    _ = create_institution_helper(client, token_b, "college-beta")

    # Member from College B tries to view College A members without membership
    res = client.get(
        f"/api/v1/institutions/{inst_a}/profiles/members",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 403
