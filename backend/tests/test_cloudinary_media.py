"""Tests for Cloudinary media integration: configuration, signatures, verification, persistence, RBAC, and isolation."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.models.event_memory import EventMemory
from app.models.institution import Institution
from app.models.media_asset import MediaAsset
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.opportunity import Opportunity, OpportunityType
from app.models.user import User


from collections.abc import Iterator
from pathlib import Path


@pytest.fixture
def media_settings(tmp_path: Path) -> Settings:
    """Settings fixture with Cloudinary explicitly enabled."""
    return Settings(
        app_env="test",
        database_url=f"sqlite:///{(tmp_path / 'media.db').as_posix()}",
        cloudinary_enabled=True,
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="123456789012345",
        cloudinary_api_secret="abcdefghijklmnopqrstuvwxyz012345",
        cloudinary_folder_prefix="eventsignal_test",
        cloudinary_max_file_size_bytes=5_242_880,
        cloudinary_allowed_formats=["jpg", "jpeg", "png", "webp", "gif"],
    )


@pytest.fixture
def disabled_media_settings(tmp_path: Path) -> Settings:
    """Settings fixture with Cloudinary disabled."""
    return Settings(
        app_env="test",
        database_url=f"sqlite:///{(tmp_path / 'disabled_media.db').as_posix()}",
        cloudinary_enabled=False,
    )


@pytest.fixture
def client(media_settings: Settings) -> Iterator[TestClient]:
    app = create_app(media_settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def disabled_client(disabled_media_settings: Settings) -> Iterator[TestClient]:
    app = create_app(disabled_media_settings)
    with TestClient(app) as c:
        yield c


def register_user(client: TestClient, email: str, full_name: str = "Test User") -> str:
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": full_name},
    )
    assert res.status_code == 201
    return res.json()["access_token"]


def create_institution(client: TestClient, token: str, slug: str) -> str:
    res = client.post(
        "/api/v1/institutions",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"Institution {slug}", "slug": slug},
    )
    assert res.status_code == 201
    return res.json()["id"]


def join_institution(client: TestClient, token: str, inst_id: str, role: str = "student") -> None:
    res = client.post(
        f"/api/v1/institutions/{inst_id}/join",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": role},
    )
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# 1. Configuration & Status Tests
# ---------------------------------------------------------------------------


def test_media_status_disabled(disabled_client: TestClient) -> None:
    res = disabled_client.get("/api/v1/media/status")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is False
    assert data["cloud_name"] is None


def test_media_status_enabled(client: TestClient) -> None:
    res = client.get("/api/v1/media/status")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is True
    assert data["cloud_name"] == "demo-cloud"
    assert "png" in data["allowed_formats"]


def test_invalid_cloudinary_configuration_rejected() -> None:
    with pytest.raises(ValueError, match="missing required settings"):
        Settings(
            app_env="test",
            database_url="sqlite:///:memory:",
            cloudinary_enabled=True,
            cloudinary_cloud_name=None,  # Missing required credentials
            cloudinary_api_key=None,
            cloudinary_api_secret=None,
        )


# ---------------------------------------------------------------------------
# 2. Upload Authorization & Signature Tests
# ---------------------------------------------------------------------------


def test_authorize_upload_unauthenticated(client: TestClient) -> None:
    res = client.post(
        "/api/v1/media/authorize-upload",
        json={"media_purpose": "opportunity_poster"},
    )
    assert res.status_code == 401


def test_authorize_upload_when_disabled(disabled_client: TestClient) -> None:
    token = register_user(disabled_client, "user_disabled@test.edu")
    res = disabled_client.post(
        "/api/v1/media/authorize-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={"media_purpose": "opportunity_poster"},
    )
    assert res.status_code == 503
    assert "disabled" in res.json()["detail"].lower()


def test_authorize_upload_success(client: TestClient) -> None:
    token = register_user(client, "author@mit.edu")
    inst_id = create_institution(client, token, "mit-tech")

    res = client.post(
        "/api/v1/media/authorize-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={"media_purpose": "opportunity_poster", "institution_id": inst_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert "signature" in data
    assert data["api_key"] == "123456789012345"
    assert data["cloud_name"] == "demo-cloud"
    assert f"eventsignal_test/{inst_id}/opportunity_poster" in data["folder"]
    assert "upload.wikimedia.org" not in data["upload_url"]
    assert "api.cloudinary.com" in data["upload_url"]


def test_authorize_upload_non_member_forbidden(client: TestClient) -> None:
    token1 = register_user(client, "admin@univ.edu")
    inst_id = create_institution(client, token1, "univ-a")

    token2 = register_user(client, "outsider@other.edu")
    res = client.post(
        "/api/v1/media/authorize-upload",
        headers={"Authorization": f"Bearer {token2}"},
        json={"media_purpose": "opportunity_poster", "institution_id": inst_id},
    )
    assert res.status_code == 403
    assert "membership is required" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Upload Verification & Metadata Safeguards
# ---------------------------------------------------------------------------


def test_complete_upload_unsupported_format(client: TestClient) -> None:
    token = register_user(client, "uploader@test.edu")
    res = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cloudinary_public_id": "eventsignal_test/global/opportunity_poster/bad_file",
            "secure_url": "https://res.cloudinary.com/demo/image/upload/bad_file.exe",
            "format": "exe",  # Not allowed
            "bytes": 1024,
        },
    )
    assert res.status_code == 400
    assert "unsupported image format" in res.json()["detail"].lower()


def test_complete_upload_excessive_size(client: TestClient) -> None:
    token = register_user(client, "uploader2@test.edu")
    res = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cloudinary_public_id": "eventsignal_test/global/opportunity_poster/giant_file",
            "secure_url": "https://res.cloudinary.com/demo/image/upload/giant_file.png",
            "format": "png",
            "bytes": 10_000_000,  # Exceeds 5MB limit
        },
    )
    assert res.status_code == 400
    assert "exceeds maximum permitted limit" in res.json()["detail"].lower()


def test_complete_upload_cross_tenant_injection_prevented(client: TestClient) -> None:
    token = register_user(client, "student_a@harvard.edu")
    inst_a = create_institution(client, token, "harvard")

    # Attempt to associate an asset belonging to another institutional folder
    res = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cloudinary_public_id": "unrelated_account_folder/evil_asset",
            "secure_url": "https://res.cloudinary.com/demo/image/upload/evil_asset.png",
            "format": "png",
            "institution_id": inst_a,
        },
    )
    assert res.status_code == 403
    assert "does not match the authorized institutional folder scope" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. End-to-End Opportunity Poster Association & Replacement
# ---------------------------------------------------------------------------


def test_opportunity_poster_lifecycle(client: TestClient) -> None:
    token = register_user(client, "lead@stanford.edu")
    inst_id = create_institution(client, token, "stanford-cs")

    # Seed opportunity record for this institution
    session = client.app.state.session_factory()
    try:
        opp = Opportunity(
            title="Apex Hackathon 2026",
            institution_id=inst_id,
            opportunity_type=OpportunityType.HACKATHON,
        )
        session.add(opp)
        session.commit()
        session.refresh(opp)
        opp_id = opp.id
    finally:
        session.close()

    # 1. Authorize poster upload
    auth_res = client.post(
        "/api/v1/media/authorize-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "media_purpose": "opportunity_poster",
            "institution_id": inst_id,
            "opportunity_id": opp_id,
        },
    )
    assert auth_res.status_code == 200

    # 2. Complete upload and associate with opportunity
    public_id = f"eventsignal_test/{inst_id}/opportunity_poster/opp_{opp_id}_poster_1"
    secure_url = f"https://res.cloudinary.com/demo-cloud/image/upload/{public_id}.png"

    comp_res = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cloudinary_public_id": public_id,
            "secure_url": secure_url,
            "format": "png",
            "bytes": 204800,
            "width": 1200,
            "height": 630,
            "alt_text": "Hackathon 2026 Official Poster",
            "media_purpose": "opportunity_poster",
            "institution_id": inst_id,
            "opportunity_id": opp_id,
        },
    )
    assert comp_res.status_code == 201
    asset_id_1 = comp_res.json()["id"]
    assert comp_res.json()["thumbnail_url"] is not None
    assert comp_res.json()["card_url"] is not None

    # 3. Verify opportunity reflects poster_url
    opp_res = client.get("/api/v1/opportunities")
    assert opp_res.status_code == 200
    items = opp_res.json()["items"]
    matched = next((o for o in items if o["id"] == opp_id), None)
    assert matched is not None
    assert matched["poster_url"] == secure_url
    assert len(matched["media_assets"]) >= 1

    # 4. Replace poster with a new version
    new_public_id = f"eventsignal_test/{inst_id}/opportunity_poster/opp_{opp_id}_poster_2"
    new_secure_url = f"https://res.cloudinary.com/demo-cloud/image/upload/{new_public_id}.png"

    replace_res = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cloudinary_public_id": new_public_id,
            "secure_url": new_secure_url,
            "format": "png",
            "bytes": 300000,
            "media_purpose": "opportunity_poster",
            "institution_id": inst_id,
            "opportunity_id": opp_id,
        },
    )
    assert replace_res.status_code == 201
    asset_id_2 = replace_res.json()["id"]

    # Old poster replaced
    opp_res_2 = client.get("/api/v1/opportunities")
    matched_2 = next((o for o in opp_res_2.json()["items"] if o["id"] == opp_id), None)
    assert matched_2 is not None
    assert matched_2["poster_url"] == new_secure_url

    # 5. Remove poster via convenience endpoint
    del_res = client.delete(
        f"/api/v1/institutions/{inst_id}/opportunities/{opp_id}/poster",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "removed"

    # Verify poster is now removed
    opp_res_3 = client.get("/api/v1/opportunities")
    matched_3 = next((o for o in opp_res_3.json()["items"] if o["id"] == opp_id), None)
    assert matched_3 is not None
    assert matched_3["poster_url"] is None


# ---------------------------------------------------------------------------
# 5. EventSignal Legacy EventMemory Media Association
# ---------------------------------------------------------------------------


def test_event_memory_media_association(client: TestClient) -> None:
    token = register_user(client, "organizer@berkeley.edu")
    inst_id = create_institution(client, token, "berkeley-eecs")

    # Create an event memory
    mem_res = client.post(
        f"/api/v1/institutions/{inst_id}/memories",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Robotics Showcase 2025 Retrospective",
            "what_worked": "Great interactive hardware booths",
            "what_did_not_work": "Power strips ran out in Hall B",
            "tags": ["robotics", "showcase"],
        },
    )
    assert mem_res.status_code == 201
    memory_id = mem_res.json()["id"]

    # Associate event memory photo
    public_id = f"eventsignal_test/{inst_id}/event_memory_media/mem_{memory_id}_photo1"
    secure_url = f"https://res.cloudinary.com/demo-cloud/image/upload/{public_id}.jpg"

    comp_res = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cloudinary_public_id": public_id,
            "secure_url": secure_url,
            "format": "jpg",
            "bytes": 500000,
            "media_purpose": "event_memory_media",
            "institution_id": inst_id,
            "event_memory_id": memory_id,
            "caption": "Hardware demo session crowd",
        },
    )
    assert comp_res.status_code == 201

    # Fetch event memories and verify media asset is included
    list_mem_res = client.get(
        f"/api/v1/institutions/{inst_id}/memories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_mem_res.status_code == 200
    items = list_mem_res.json()["items"]
    memory_record = next((m for m in items if m["id"] == memory_id), None)
    assert memory_record is not None
    assert len(memory_record["media_assets"]) == 1
    assert memory_record["media_assets"][0]["caption"] == "Hardware demo session crowd"


# ---------------------------------------------------------------------------
# 6. Deletion and RBAC Enforcement
# ---------------------------------------------------------------------------


def test_delete_media_asset_unauthorized_forbidden(client: TestClient) -> None:
    token1 = register_user(client, "owner@caltech.edu")
    inst_id = create_institution(client, token1, "caltech")

    # Upload an asset
    public_id = f"eventsignal_test/{inst_id}/opportunity_poster/caltech_poster"
    res1 = client.post(
        "/api/v1/media/complete-upload",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "cloudinary_public_id": public_id,
            "secure_url": f"https://res.cloudinary.com/demo-cloud/{public_id}.png",
            "format": "png",
            "institution_id": inst_id,
        },
    )
    assert res1.status_code == 201
    asset_id = res1.json()["id"]

    # Different user attempts to delete it
    token2 = register_user(client, "intruder@other.edu")
    del_res = client.delete(
        f"/api/v1/media/{asset_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert del_res.status_code == 403
