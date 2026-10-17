"""Institution and multi-college workspace management API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_optional_current_user,
    require_institution_admin_access,
)
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.institution import InstitutionStatus
from app.models.membership import InstitutionRole, MembershipStatus
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.campus_position import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentVerifyRequest,
    PositionCreate,
    PositionResponse,
)
from app.schemas.institution import (
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
    InstitutionWorkspaceSummary,
)
from app.schemas.membership import (
    MembershipCreate,
    MembershipResponse,
    MembershipSelfJoin,
    MembershipUpdateRole,
    MembershipUpdateStatus,
)
from app.schemas.organizational_unit import UnitCreate, UnitResponse, UnitUpdate
from app.services.institution import (
    InstitutionError,
    add_member,
    assign_role,
    create_institution,
    create_position,
    create_unit,
    get_institution,
    get_workspace_summary,
    list_assignments,
    list_institutions,
    list_members,
    list_positions,
    list_units,
    update_institution,
    update_member_role,
    update_member_status,
    update_unit,
    verify_assignment,
)

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.post(
    "",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new college workspace",
)
def create_new_institution(
    payload: InstitutionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> InstitutionResponse:
    """Register a new institution. If called by an authenticated user, they become its admin."""
    try:
        inst = create_institution(
            session=db,
            data=payload,
            actor_user_id=current_user.id if current_user else None,
        )
    except InstitutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    db.commit()
    return InstitutionResponse.model_validate(inst)


@router.get(
    "",
    response_model=list[InstitutionResponse],
    summary="List all institutions",
)
def get_all_institutions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    status_filter: Annotated[InstitutionStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[InstitutionResponse]:
    """Retrieve list of institutions."""
    from app.services.demo_service import DEMO_INSTITUTION_ID, DemoService

    institutions = list_institutions(db, status=status_filter, limit=limit, offset=offset)
    is_demo = bool(current_user and DemoService.is_demo_user(current_user))
    if not is_demo:
        # Hide private demonstration institution from ordinary users and guests
        institutions = [inst for inst in institutions if inst.id != DEMO_INSTITUTION_ID]

    return [InstitutionResponse.model_validate(inst) for inst in institutions]


@router.get(
    "/{institution_id}",
    response_model=InstitutionResponse,
    summary="Get institution by ID or slug",
)
def get_institution_by_id(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> InstitutionResponse:
    """Retrieve details for a single institution workspace."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    return InstitutionResponse.model_validate(inst)


@router.patch(
    "/{institution_id}",
    response_model=InstitutionResponse,
    summary="Update institution details",
)
def update_institution_details(
    institution_id: str,
    payload: InstitutionUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> InstitutionResponse:
    """Update institution properties (institution or platform admin only)."""
    try:
        inst = update_institution(
            session=db,
            institution_id=institution_id,
            data=payload,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return InstitutionResponse.model_validate(inst)


@router.get(
    "/{institution_id}/workspace",
    response_model=InstitutionWorkspaceSummary,
    summary="Get aggregated workspace summary metrics",
)
def get_workspace_metrics(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> InstitutionWorkspaceSummary:
    """Retrieve high-level workspace health and activity metrics."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    summary = get_workspace_summary(db, inst.id)
    return InstitutionWorkspaceSummary(
        institution=InstitutionResponse.model_validate(summary["institution"]),
        total_members=summary["total_members"],
        total_units=summary["total_units"],
        total_positions=summary["total_positions"],
        active_assignments=summary["active_assignments"],
        total_opportunities=summary["total_opportunities"],
    )


# ---- Memberships ----


@router.get(
    "/{institution_id}/members",
    response_model=list[MembershipResponse],
    summary="List members in this institutional workspace",
)
def list_workspace_members(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    role: InstitutionRole | None = None,
    membership_status: Annotated[MembershipStatus | None, Query(alias="status")] = None,
) -> list[MembershipResponse]:
    """List members affiliated with the institution."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    members = list_members(db, inst.id, role=role, status=membership_status)
    return [
        MembershipResponse(
            id=m.id,
            institution_id=m.institution_id,
            user_id=m.user_id,
            role=m.role,
            status=m.status,
            joined_at=m.joined_at,
            verified_at=m.verified_at,
            verified_by_user_id=m.verified_by_user_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
            user_email=m.user.email if m.user else None,
            user_full_name=m.user.full_name if m.user else None,
        )
        for m in members
    ]


@router.post(
    "/{institution_id}/members",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an authorized member to this workspace",
)
def add_workspace_member(
    institution_id: str,
    payload: MembershipCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> MembershipResponse:
    """Add member with explicit role (institution admin only)."""
    try:
        membership = add_member(
            session=db,
            institution_id=institution_id,
            user_id=payload.user_id,
            role=payload.role,
            status=payload.status,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(membership)

    return MembershipResponse(
        id=membership.id,
        institution_id=membership.institution_id,
        user_id=membership.user_id,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        verified_at=membership.verified_at,
        verified_by_user_id=membership.verified_by_user_id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
        user_email=membership.user.email if membership.user else None,
        user_full_name=membership.user.full_name if membership.user else None,
    )


@router.post(
    "/{institution_id}/join",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join an institutional workspace as student, faculty, or alumni",
)
def join_workspace(
    institution_id: str,
    payload: MembershipSelfJoin,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MembershipResponse:
    """Self-join a college workspace."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    try:
        membership = add_member(
            session=db,
            institution_id=inst.id,
            user_id=current_user.id,
            role=payload.role,
            status=MembershipStatus.ACTIVE,
            actor_user_id=current_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(membership)

    return MembershipResponse(
        id=membership.id,
        institution_id=membership.institution_id,
        user_id=membership.user_id,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        verified_at=membership.verified_at,
        verified_by_user_id=membership.verified_by_user_id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
        user_email=current_user.email,
        user_full_name=current_user.full_name,
    )


@router.patch(
    "/{institution_id}/members/{user_id}/role",
    response_model=MembershipResponse,
    summary="Update a member's institutional role",
)
def change_member_role(
    institution_id: str,
    user_id: str,
    payload: MembershipUpdateRole,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> MembershipResponse:
    """Update role for an institutional member (institution admin only)."""
    try:
        membership = update_member_role(
            session=db,
            institution_id=institution_id,
            user_id=user_id,
            new_role=payload.role,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(membership)

    return MembershipResponse(
        id=membership.id,
        institution_id=membership.institution_id,
        user_id=membership.user_id,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        verified_at=membership.verified_at,
        verified_by_user_id=membership.verified_by_user_id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
        user_email=membership.user.email if membership.user else None,
        user_full_name=membership.user.full_name if membership.user else None,
    )


@router.patch(
    "/{institution_id}/members/{user_id}/status",
    response_model=MembershipResponse,
    summary="Update a member's lifecycle status",
)
def change_member_status(
    institution_id: str,
    user_id: str,
    payload: MembershipUpdateStatus,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> MembershipResponse:
    """Update member status (e.g., active, suspended, revoked)."""
    try:
        membership = update_member_status(
            session=db,
            institution_id=institution_id,
            user_id=user_id,
            new_status=payload.status,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(membership)

    return MembershipResponse(
        id=membership.id,
        institution_id=membership.institution_id,
        user_id=membership.user_id,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        verified_at=membership.verified_at,
        verified_by_user_id=membership.verified_by_user_id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
        user_email=membership.user.email if membership.user else None,
        user_full_name=membership.user.full_name if membership.user else None,
    )


# ---- Organizational Units ----


@router.get(
    "/{institution_id}/units",
    response_model=list[UnitResponse],
    summary="List organizational units (departments, cells, offices)",
)
def list_institution_units(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> list[UnitResponse]:
    """Retrieve organizational units belonging to this institution."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    units = list_units(db, inst.id)
    return [UnitResponse.model_validate(u) for u in units]


@router.post(
    "/{institution_id}/units",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organizational unit",
)
def create_institution_unit(
    institution_id: str,
    payload: UnitCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> UnitResponse:
    """Create a new department, cell, or office (institution admin only)."""
    try:
        unit = create_unit(
            session=db,
            institution_id=institution_id,
            data=payload,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(unit)
    return UnitResponse.model_validate(unit)


@router.patch(
    "/{institution_id}/units/{unit_id}",
    response_model=UnitResponse,
    summary="Update an organizational unit",
)
def update_institution_unit(
    institution_id: str,
    unit_id: str,
    payload: UnitUpdate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> UnitResponse:
    """Update department or cell properties."""
    try:
        unit = update_unit(
            session=db,
            institution_id=institution_id,
            unit_id=unit_id,
            data=payload,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(unit)
    return UnitResponse.model_validate(unit)


# ---- Campus Positions & Role Assignments ----


@router.get(
    "/{institution_id}/positions",
    response_model=list[PositionResponse],
    summary="List defined official campus positions",
)
def list_institution_positions(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    unit_id: str | None = None,
) -> list[PositionResponse]:
    """Retrieve official positions defined by the institution."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    positions = list_positions(db, inst.id, unit_id=unit_id)
    return [PositionResponse.model_validate(p) for p in positions]


@router.post(
    "/{institution_id}/positions",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define an official campus position",
)
def create_institution_position(
    institution_id: str,
    payload: PositionCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> PositionResponse:
    """Catalogue a leadership or campus role (e.g. Placement Coordinator)."""
    try:
        position = create_position(
            session=db,
            institution_id=institution_id,
            data=payload,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(position)
    return PositionResponse.model_validate(position)


@router.get(
    "/{institution_id}/assignments",
    response_model=list[AssignmentResponse],
    summary="List appointed campus positions",
)
def list_institution_assignments(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: str | None = None,
    position_id: str | None = None,
    active_only: Annotated[bool, Query()] = False,
) -> list[AssignmentResponse]:
    """List appointed campus roles and verified tenures."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    assignments = list_assignments(
        db,
        inst.id,
        user_id=user_id,
        position_id=position_id,
        active_only=active_only,
    )
    return [
        AssignmentResponse(
            id=a.id,
            institution_id=a.institution_id,
            user_id=a.user_id,
            position_id=a.position_id,
            unit_id=a.unit_id,
            start_date=a.start_date,
            end_date=a.end_date,
            is_active=a.is_active,
            verification_status=a.verification_status,
            verified_at=a.verified_at,
            verified_by_user_id=a.verified_by_user_id,
            created_at=a.created_at,
            updated_at=a.updated_at,
            user_full_name=a.user.full_name if a.user else None,
            user_email=a.user.email if a.user else None,
            position_title=a.position.title if a.position else None,
            unit_name=a.unit.name if a.unit else None,
        )
        for a in assignments
    ]


@router.post(
    "/{institution_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Appoint a user to an official campus position",
)
def create_role_appointment(
    institution_id: str,
    payload: AssignmentCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> AssignmentResponse:
    """Appoint user to official campus position with time-bounded tenure."""
    try:
        assignment = assign_role(
            session=db,
            institution_id=institution_id,
            data=payload,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        institution_id=assignment.institution_id,
        user_id=assignment.user_id,
        position_id=assignment.position_id,
        unit_id=assignment.unit_id,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        is_active=assignment.is_active,
        verification_status=assignment.verification_status,
        verified_at=assignment.verified_at,
        verified_by_user_id=assignment.verified_by_user_id,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        user_full_name=assignment.user.full_name if assignment.user else None,
        user_email=assignment.user.email if assignment.user else None,
        position_title=assignment.position.title if assignment.position else None,
        unit_name=assignment.unit.name if assignment.unit else None,
    )


@router.post(
    "/{institution_id}/assignments/{assignment_id}/verify",
    response_model=AssignmentResponse,
    summary="Officially verify or reject a campus position appointment",
)
def verify_role_appointment(
    institution_id: str,
    assignment_id: str,
    payload: AssignmentVerifyRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
) -> AssignmentResponse:
    """Verify or reject appointment (institution admin only)."""
    try:
        assignment = verify_assignment(
            session=db,
            institution_id=institution_id,
            assignment_id=assignment_id,
            status=payload.verification_status,
            actor_user_id=admin_user.id,
        )
    except InstitutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        institution_id=assignment.institution_id,
        user_id=assignment.user_id,
        position_id=assignment.position_id,
        unit_id=assignment.unit_id,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        is_active=assignment.is_active,
        verification_status=assignment.verification_status,
        verified_at=assignment.verified_at,
        verified_by_user_id=assignment.verified_by_user_id,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        user_full_name=assignment.user.full_name if assignment.user else None,
        user_email=assignment.user.email if assignment.user else None,
        position_title=assignment.position.title if assignment.position else None,
        unit_name=assignment.unit.name if assignment.unit else None,
    )


# ---- Security Audit Trail ----


@router.get(
    "/{institution_id}/audit-logs",
    response_model=list[AuditLogResponse],
    summary="View institutional security and administrative audit log",
)
def get_institution_audit_trail(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_institution_admin_access)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditLogResponse]:
    """Retrieve audit events for this institution workspace (admin only)."""
    inst = get_institution(db, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    logs = list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.institution_id == inst.id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
