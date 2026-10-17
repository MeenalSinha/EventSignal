"""Pydantic schemas for institution memberships and RBAC."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.membership import InstitutionRole, MembershipStatus


class MembershipCreate(BaseModel):
    """Payload to add a user to an institutional workspace."""

    user_id: str
    role: InstitutionRole = InstitutionRole.STUDENT
    status: MembershipStatus = MembershipStatus.ACTIVE


class MembershipSelfJoin(BaseModel):
    """Payload for an authenticated student/alumni/faculty to join an institution."""

    role: InstitutionRole = InstitutionRole.STUDENT


class MembershipUpdateRole(BaseModel):
    """Payload to alter an institutional member's role."""

    role: InstitutionRole


class MembershipUpdateStatus(BaseModel):
    """Payload to change an institutional member's lifecycle status."""

    status: MembershipStatus


class MembershipResponse(BaseModel):
    """Membership record with user details."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    user_id: str
    role: InstitutionRole
    status: MembershipStatus
    joined_at: datetime
    verified_at: datetime | None
    verified_by_user_id: str | None
    created_at: datetime
    updated_at: datetime
    user_email: str | None = None
    user_full_name: str | None = None
