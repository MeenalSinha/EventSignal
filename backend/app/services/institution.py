"""Institution and workspace management service.

Handles multi-college onboarding, organizational units, institutional memberships (RBAC),
official campus leadership positions, and time-bounded role assignments.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.campus_position import (
    AssignmentVerificationStatus,
    CampusPositionDefinition,
    CampusRoleAssignment,
)
from app.models.institution import (
    Institution,
    InstitutionStatus,
    InstitutionVerificationStatus,
)
from app.models.membership import (
    InstitutionMembership,
    InstitutionRole,
    MembershipStatus,
)
from app.models.opportunity import Opportunity
from app.models.organizational_unit import OrganizationalUnit
from app.models.user import User
from app.schemas.campus_position import AssignmentCreate, PositionCreate
from app.schemas.institution import InstitutionCreate, InstitutionUpdate
from app.schemas.organizational_unit import UnitCreate, UnitUpdate
from app.services.audit import record_audit_event

logger = logging.getLogger(__name__)


class InstitutionError(ValueError):
    """Raised for invalid institution operations."""


class PermissionDeniedError(ValueError):
    """Raised when an actor lacks authority for an operation."""


def create_institution(
    session: Session,
    data: InstitutionCreate,
    actor_user_id: str | None = None,
) -> Institution:
    """Create a new institution workspace."""
    slug = data.slug.strip().lower()
    existing_slug = session.scalar(select(Institution).where(Institution.slug == slug))
    if existing_slug:
        raise InstitutionError(f"Institution slug '{slug}' is already taken")

    institution = Institution(
        name=data.name.strip(),
        slug=slug,
        domain=data.domain.strip().lower() if data.domain else None,
        description=data.description,
        location=data.location,
        contact_email=data.contact_email,
        website_url=data.website_url,
        status=InstitutionStatus.ACTIVE,
        verification_status=InstitutionVerificationStatus.UNVERIFIED,
        extra_data=data.extra_data,
    )
    session.add(institution)
    session.flush()

    # If created by an authenticated user, make them the initial institution admin
    if actor_user_id:
        membership = InstitutionMembership(
            institution_id=institution.id,
            user_id=actor_user_id,
            role=InstitutionRole.INSTITUTION_ADMIN,
            status=MembershipStatus.ACTIVE,
            verified_at=utcnow(),
            verified_by_user_id=actor_user_id,
        )
        session.add(membership)
        session.flush()

    record_audit_event(
        session=session,
        action="institution.created",
        target_type="institution",
        target_id=institution.id,
        actor_user_id=actor_user_id,
        institution_id=institution.id,
        details={"name": institution.name, "slug": institution.slug},
    )

    return institution


def get_institution(session: Session, identifier: str) -> Institution | None:
    """Find institution by ID or slug."""
    clean = identifier.strip().lower()
    return session.scalar(
        select(Institution).where(or_(Institution.id == identifier, Institution.slug == clean))
    )


def list_institutions(
    session: Session,
    status: InstitutionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Institution]:
    """List institutions."""
    stmt = select(Institution).order_by(Institution.name.asc())
    if status:
        stmt = stmt.where(Institution.status == status)
    return list(session.scalars(stmt.limit(limit).offset(offset)))


def update_institution(
    session: Session,
    institution_id: str,
    data: InstitutionUpdate,
    actor_user_id: str | None = None,
) -> Institution:
    """Update institution properties."""
    inst = session.get(Institution, institution_id)
    if not inst:
        raise InstitutionError("Institution not found")

    if data.name is not None:
        inst.name = data.name.strip()
    if data.domain is not None:
        inst.domain = data.domain.strip().lower()
    if data.description is not None:
        inst.description = data.description
    if data.location is not None:
        inst.location = data.location
    if data.contact_email is not None:
        inst.contact_email = data.contact_email
    if data.website_url is not None:
        inst.website_url = data.website_url
    if data.status is not None:
        inst.status = data.status
    if data.verification_status is not None:
        inst.verification_status = data.verification_status
        if data.verification_status == InstitutionVerificationStatus.VERIFIED:
            inst.verified_at = utcnow()
        else:
            inst.verified_at = None
    if data.extra_data is not None:
        inst.extra_data = data.extra_data

    session.flush()

    record_audit_event(
        session=session,
        action="institution.updated",
        target_type="institution",
        target_id=inst.id,
        actor_user_id=actor_user_id,
        institution_id=inst.id,
        details={"status": inst.status, "verification": inst.verification_status},
    )

    return inst


def get_workspace_summary(session: Session, institution_id: str) -> dict[str, Any]:
    """Compute workspace metrics for an institution."""
    inst = session.get(Institution, institution_id)
    if not inst:
        raise InstitutionError("Institution not found")

    member_count = (
        session.scalar(
            select(func.count(InstitutionMembership.id)).where(
                InstitutionMembership.institution_id == institution_id
            )
        )
        or 0
    )

    unit_count = (
        session.scalar(
            select(func.count(OrganizationalUnit.id)).where(
                OrganizationalUnit.institution_id == institution_id
            )
        )
        or 0
    )

    position_count = (
        session.scalar(
            select(func.count(CampusPositionDefinition.id)).where(
                CampusPositionDefinition.institution_id == institution_id
            )
        )
        or 0
    )

    active_assignments = (
        session.scalar(
            select(func.count(CampusRoleAssignment.id)).where(
                CampusRoleAssignment.institution_id == institution_id,
                CampusRoleAssignment.is_active.is_(True),
            )
        )
        or 0
    )

    opp_count = (
        session.scalar(
            select(func.count(Opportunity.id)).where(Opportunity.institution_id == institution_id)
        )
        or 0
    )

    return {
        "institution": inst,
        "total_members": member_count,
        "total_units": unit_count,
        "total_positions": position_count,
        "active_assignments": active_assignments,
        "total_opportunities": opp_count,
    }


# ---- Membership & RBAC ----


def add_member(
    session: Session,
    institution_id: str,
    user_id: str,
    role: InstitutionRole = InstitutionRole.STUDENT,
    status: MembershipStatus = MembershipStatus.ACTIVE,
    actor_user_id: str | None = None,
) -> InstitutionMembership:
    """Add user to institution with role."""
    inst = session.get(Institution, institution_id)
    if not inst:
        raise InstitutionError("Institution not found")
    user = session.get(User, user_id)
    if not user:
        raise InstitutionError("User not found")

    existing = session.scalar(
        select(InstitutionMembership).where(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.user_id == user_id,
        )
    )
    if existing:
        raise InstitutionError("User is already a member of this institution")

    membership = InstitutionMembership(
        institution_id=institution_id,
        user_id=user_id,
        role=role,
        status=status,
        joined_at=utcnow(),
        verified_by_user_id=actor_user_id,
        verified_at=utcnow() if status == MembershipStatus.ACTIVE else None,
    )
    session.add(membership)
    session.flush()

    record_audit_event(
        session=session,
        action="membership.added",
        target_type="membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"user_id": user_id, "role": role, "status": status},
    )

    return membership


def list_members(
    session: Session,
    institution_id: str,
    role: InstitutionRole | None = None,
    status: MembershipStatus | None = None,
) -> list[InstitutionMembership]:
    """List members of an institution."""
    stmt = (
        select(InstitutionMembership)
        .where(InstitutionMembership.institution_id == institution_id)
        .order_by(InstitutionMembership.joined_at.desc())
    )
    if role:
        stmt = stmt.where(InstitutionMembership.role == role)
    if status:
        stmt = stmt.where(InstitutionMembership.status == status)
    return list(session.scalars(stmt))


def get_member(session: Session, institution_id: str, user_id: str) -> InstitutionMembership | None:
    """Get specific membership."""
    return session.scalar(
        select(InstitutionMembership).where(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.user_id == user_id,
        )
    )


def update_member_role(
    session: Session,
    institution_id: str,
    user_id: str,
    new_role: InstitutionRole,
    actor_user_id: str | None = None,
) -> InstitutionMembership:
    """Update role for a member."""
    membership = get_member(session, institution_id, user_id)
    if not membership:
        raise InstitutionError("Membership not found")

    old_role = membership.role
    membership.role = new_role
    session.flush()

    record_audit_event(
        session=session,
        action="membership.role_updated",
        target_type="membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"old_role": old_role, "new_role": new_role},
    )

    return membership


def update_member_status(
    session: Session,
    institution_id: str,
    user_id: str,
    new_status: MembershipStatus,
    actor_user_id: str | None = None,
) -> InstitutionMembership:
    """Update membership lifecycle status."""
    membership = get_member(session, institution_id, user_id)
    if not membership:
        raise InstitutionError("Membership not found")

    old_status = membership.status
    membership.status = new_status
    if new_status == MembershipStatus.ACTIVE and not membership.verified_at:
        membership.verified_at = utcnow()
        membership.verified_by_user_id = actor_user_id

    session.flush()

    record_audit_event(
        session=session,
        action="membership.status_updated",
        target_type="membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"old_status": old_status, "new_status": new_status},
    )

    return membership


# ---- Organizational Units ----


def create_unit(
    session: Session,
    institution_id: str,
    data: UnitCreate,
    actor_user_id: str | None = None,
) -> OrganizationalUnit:
    """Create an organizational unit."""
    inst = session.get(Institution, institution_id)
    if not inst:
        raise InstitutionError("Institution not found")

    if data.parent_id:
        parent = session.get(OrganizationalUnit, data.parent_id)
        if not parent or parent.institution_id != institution_id:
            raise InstitutionError("Invalid parent unit specified")

    unit = OrganizationalUnit(
        institution_id=institution_id,
        name=data.name.strip(),
        code=data.code.strip() if data.code else None,
        unit_type=data.unit_type.strip(),
        parent_id=data.parent_id,
        description=data.description,
        contact_email=data.contact_email,
    )
    session.add(unit)
    session.flush()

    record_audit_event(
        session=session,
        action="unit.created",
        target_type="organizational_unit",
        target_id=unit.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"name": unit.name, "code": unit.code},
    )

    return unit


def list_units(session: Session, institution_id: str) -> list[OrganizationalUnit]:
    """List organizational units of an institution."""
    return list(
        session.scalars(
            select(OrganizationalUnit)
            .where(OrganizationalUnit.institution_id == institution_id)
            .order_by(OrganizationalUnit.name.asc())
        )
    )


def update_unit(
    session: Session,
    institution_id: str,
    unit_id: str,
    data: UnitUpdate,
    actor_user_id: str | None = None,
) -> OrganizationalUnit:
    """Update organizational unit."""
    unit = session.get(OrganizationalUnit, unit_id)
    if not unit or unit.institution_id != institution_id:
        raise InstitutionError("Organizational unit not found")

    if data.name is not None:
        unit.name = data.name.strip()
    if data.code is not None:
        unit.code = data.code.strip()
    if data.unit_type is not None:
        unit.unit_type = data.unit_type.strip()
    if data.parent_id is not None:
        if data.parent_id == unit_id:
            raise InstitutionError("Unit cannot be its own parent")
        unit.parent_id = data.parent_id
    if data.description is not None:
        unit.description = data.description
    if data.contact_email is not None:
        unit.contact_email = data.contact_email

    session.flush()

    record_audit_event(
        session=session,
        action="unit.updated",
        target_type="organizational_unit",
        target_id=unit.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"name": unit.name},
    )

    return unit


# ---- Campus Positions & Role Assignments ----


def create_position(
    session: Session,
    institution_id: str,
    data: PositionCreate,
    actor_user_id: str | None = None,
) -> CampusPositionDefinition:
    """Define a new official campus position."""
    inst = session.get(Institution, institution_id)
    if not inst:
        raise InstitutionError("Institution not found")

    if data.unit_id:
        unit = session.get(OrganizationalUnit, data.unit_id)
        if not unit or unit.institution_id != institution_id:
            raise InstitutionError("Invalid organizational unit")

    position = CampusPositionDefinition(
        institution_id=institution_id,
        unit_id=data.unit_id,
        title=data.title.strip(),
        description=data.description,
        is_leadership=data.is_leadership,
    )
    session.add(position)
    session.flush()

    record_audit_event(
        session=session,
        action="position.created",
        target_type="campus_position_definition",
        target_id=position.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"title": position.title, "is_leadership": position.is_leadership},
    )

    return position


def list_positions(
    session: Session, institution_id: str, unit_id: str | None = None
) -> list[CampusPositionDefinition]:
    """List positions in institution."""
    stmt = (
        select(CampusPositionDefinition)
        .where(CampusPositionDefinition.institution_id == institution_id)
        .order_by(CampusPositionDefinition.title.asc())
    )
    if unit_id:
        stmt = stmt.where(CampusPositionDefinition.unit_id == unit_id)
    return list(session.scalars(stmt))


def assign_role(
    session: Session,
    institution_id: str,
    data: AssignmentCreate,
    actor_user_id: str | None = None,
) -> CampusRoleAssignment:
    """Appoint a user to a campus position."""
    inst = session.get(Institution, institution_id)
    if not inst:
        raise InstitutionError("Institution not found")
    user = session.get(User, data.user_id)
    if not user:
        raise InstitutionError("User not found")
    pos = session.get(CampusPositionDefinition, data.position_id)
    if not pos or pos.institution_id != institution_id:
        raise InstitutionError("Position does not belong to this institution")

    assignment = CampusRoleAssignment(
        institution_id=institution_id,
        user_id=data.user_id,
        position_id=data.position_id,
        unit_id=data.unit_id or pos.unit_id,
        start_date=data.start_date,
        end_date=data.end_date,
        is_active=data.is_active,
        verification_status=AssignmentVerificationStatus.UNVERIFIED,
    )
    session.add(assignment)
    session.flush()

    record_audit_event(
        session=session,
        action="assignment.created",
        target_type="campus_role_assignment",
        target_id=assignment.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={
            "user_id": data.user_id,
            "position_id": data.position_id,
            "start_date": str(data.start_date),
        },
    )

    return assignment


def list_assignments(
    session: Session,
    institution_id: str,
    user_id: str | None = None,
    position_id: str | None = None,
    active_only: bool = False,
) -> list[CampusRoleAssignment]:
    """List appointments in an institution."""
    stmt = (
        select(CampusRoleAssignment)
        .where(CampusRoleAssignment.institution_id == institution_id)
        .order_by(CampusRoleAssignment.start_date.desc())
    )
    if user_id:
        stmt = stmt.where(CampusRoleAssignment.user_id == user_id)
    if position_id:
        stmt = stmt.where(CampusRoleAssignment.position_id == position_id)
    if active_only:
        stmt = stmt.where(CampusRoleAssignment.is_active.is_(True))
    return list(session.scalars(stmt))


def verify_assignment(
    session: Session,
    institution_id: str,
    assignment_id: str,
    status: AssignmentVerificationStatus,
    actor_user_id: str | None = None,
) -> CampusRoleAssignment:
    """Verify or reject an official campus role assignment."""
    assignment = session.get(CampusRoleAssignment, assignment_id)
    if not assignment or assignment.institution_id != institution_id:
        raise InstitutionError("Assignment not found")

    assignment.verification_status = status
    if status == AssignmentVerificationStatus.VERIFIED:
        assignment.verified_at = utcnow()
        assignment.verified_by_user_id = actor_user_id
    else:
        assignment.verified_at = None
        assignment.verified_by_user_id = None

    session.flush()

    record_audit_event(
        session=session,
        action="assignment.verified",
        target_type="campus_role_assignment",
        target_id=assignment.id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details={"status": status},
    )

    return assignment
