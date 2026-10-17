"""Tests for multi-college institutional identity, workspaces, units, positions, and RBAC."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.campus_position import AssignmentVerificationStatus
from app.models.membership import InstitutionRole


def _create_authenticated_user(
    client: TestClient, email: str, name: str, password: str = "TestPassword123!"
) -> tuple[str, str]:
    """Helper to register and return (user_id, bearer_token)."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    user_id = me_resp.json()["user"]["id"]
    return user_id, token


def test_institution_workspace_lifecycle(client: TestClient) -> None:
    # 1. Register college admin
    admin_id, admin_token = _create_authenticated_user(
        client, "dean@iiitd.ac.in", "Prof. Pankaj Jalote"
    )

    # 2. Create institution workspace
    create_resp = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Indraprastha Institute of Information Technology Delhi",
            "slug": "iiitd",
            "domain": "iiitd.ac.in",
            "description": "State university focused on IT and interdisciplinary research.",
            "location": "Okhla Phase III, New Delhi",
            "contact_email": "admin@iiitd.ac.in",
            "website_url": "https://iiitd.ac.in",
        },
    )
    assert create_resp.status_code == 201
    inst_data = create_resp.json()
    assert inst_data["name"] == "Indraprastha Institute of Information Technology Delhi"
    assert inst_data["slug"] == "iiitd"
    inst_id = inst_data["id"]

    # 3. Duplicate slug fails with 409
    dup_resp = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "IIIT Delhi Duplicate",
            "slug": "iiitd",
        },
    )
    assert dup_resp.status_code == 409

    # 4. List institutions
    list_resp = client.get("/api/v1/institutions")
    assert list_resp.status_code == 200
    institutions = list_resp.json()
    assert any(i["id"] == inst_id for i in institutions)

    # 5. Get institution by ID and by slug
    get_by_id = client.get(f"/api/v1/institutions/{inst_id}")
    assert get_by_id.status_code == 200
    assert get_by_id.json()["slug"] == "iiitd"

    get_by_slug = client.get("/api/v1/institutions/iiitd")
    assert get_by_slug.status_code == 200
    assert get_by_slug.json()["id"] == inst_id

    # 6. Creator is automatically an institution admin in membership
    members_resp = client.get(
        f"/api/v1/institutions/{inst_id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert members_resp.status_code == 200
    members = members_resp.json()
    assert len(members) == 1
    assert members[0]["user_id"] == admin_id
    assert members[0]["role"] == InstitutionRole.INSTITUTION_ADMIN.value


def test_membership_rbac_and_isolation(client: TestClient) -> None:
    _admin_id, admin_token = _create_authenticated_user(client, "admin2@nsut.ac.in", "NSUT Admin")
    inst_resp = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Netaji Subhas University of Technology", "slug": "nsut"},
    )
    inst_id = inst_resp.json()["id"]

    student_id, student_token = _create_authenticated_user(
        client, "student@nsut.ac.in", "Student Rahul"
    )

    # 1. Student self-joins NSUT workspace as student
    join_resp = client.post(
        f"/api/v1/institutions/{inst_id}/join",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"role": "student"},
    )
    assert join_resp.status_code == 201
    assert join_resp.json()["role"] == "student"

    # 2. Student tries to add another member -> 403 Forbidden
    other_id, _ = _create_authenticated_user(client, "other@nsut.ac.in", "Other User")
    forbidden_add = client.post(
        f"/api/v1/institutions/{inst_id}/members",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"user_id": other_id, "role": "faculty"},
    )
    assert forbidden_add.status_code == 403

    # 3. Admin promotes student to faculty
    promote_resp = client.patch(
        f"/api/v1/institutions/{inst_id}/members/{student_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "faculty"},
    )
    assert promote_resp.status_code == 200
    assert promote_resp.json()["role"] == "faculty"

    # 4. Admin suspends student membership
    suspend_resp = client.patch(
        f"/api/v1/institutions/{inst_id}/members/{student_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "suspended"},
    )
    assert suspend_resp.status_code == 200
    assert suspend_resp.json()["status"] == "suspended"


def test_organizational_units_and_official_positions(client: TestClient) -> None:
    admin_id, admin_token = _create_authenticated_user(client, "admin@dtu.ac.in", "DTU Admin")
    inst_resp = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Delhi Technological University", "slug": "dtu"},
    )
    inst_id = inst_resp.json()["id"]

    # 1. Create Organizational Unit (Department)
    dept_resp = client.post(
        f"/api/v1/institutions/{inst_id}/units",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Department of Computer Science & Engineering",
            "code": "CSE",
            "unit_type": "academic_department",
            "description": "Leading department for CS research and education.",
        },
    )
    assert dept_resp.status_code == 201
    unit_id = dept_resp.json()["id"]

    # 2. Create sub-unit (T&P Cell)
    cell_resp = client.post(
        f"/api/v1/institutions/{inst_id}/units",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Training & Placement Cell",
            "code": "TPO",
            "unit_type": "administrative_office",
            "parent_id": unit_id,
        },
    )
    assert cell_resp.status_code == 201
    cell_id = cell_resp.json()["id"]

    # 3. List units
    units_list = client.get(f"/api/v1/institutions/{inst_id}/units")
    assert units_list.status_code == 200
    assert len(units_list.json()) == 2

    # 4. Define official campus leadership position
    pos_resp = client.post(
        f"/api/v1/institutions/{inst_id}/positions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Lead Placement Coordinator",
            "unit_id": cell_id,
            "description": "Oversees internship and placement drives for the department.",
            "is_leadership": True,
        },
    )
    assert pos_resp.status_code == 201
    pos_id = pos_resp.json()["id"]
    assert pos_resp.json()["is_leadership"] is True

    # 5. Appoint a user to this position for a time-bounded tenure
    lead_user_id, _ = _create_authenticated_user(client, "lead@dtu.ac.in", "Pooja Sharma")
    # First add Pooja as member
    client.post(
        f"/api/v1/institutions/{inst_id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": lead_user_id, "role": "student"},
    )

    now = datetime.now(UTC)
    start_date = now.isoformat()
    end_date = (now + timedelta(days=365)).isoformat()

    assign_resp = client.post(
        f"/api/v1/institutions/{inst_id}/assignments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "user_id": lead_user_id,
            "position_id": pos_id,
            "unit_id": cell_id,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": True,
        },
    )
    assert assign_resp.status_code == 201
    assignment = assign_resp.json()
    assert assignment["verification_status"] == AssignmentVerificationStatus.UNVERIFIED.value
    assignment_id = assignment["id"]

    # 6. Verify appointment
    verify_resp = client.post(
        f"/api/v1/institutions/{inst_id}/assignments/{assignment_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"verification_status": "verified"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verification_status"] == "verified"
    assert verify_resp.json()["verified_by_user_id"] == admin_id

    # 7. Check workspace summary metrics
    summary_resp = client.get(f"/api/v1/institutions/{inst_id}/workspace")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_members"] == 2
    assert summary["total_units"] == 2
    assert summary["total_positions"] == 1
    assert summary["active_assignments"] == 1

    # 8. Check security audit trail
    audit_resp = client.get(
        f"/api/v1/institutions/{inst_id}/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) >= 4  # institution created, unit created, position created, assigned, verified
    actions = [log["action"] for log in logs]
    assert "institution.created" in actions
    assert "assignment.verified" in actions
