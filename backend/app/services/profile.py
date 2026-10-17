"""Profile management and privacy-aware member discovery service.

Encapsulates business rules for StudentProfile, AlumniProfile, visibility enums,
and tenant-isolated campus directory search.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.alumni_profile import AlumniProfile
from app.models.alumni_profile import ProfileVisibility as AlumniVisibility
from app.models.campus_position import CampusRoleAssignment
from app.models.help_offer import HelpOffer, HelpOfferStatus
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.student_profile import ProfileVisibility as StudentVisibility
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.profile import (
    AlumniProfileCreate,
    AlumniProfileRead,
    AlumniProfileUpdate,
    MemberDiscoveryRead,
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
)


def _ensure_active_membership(
    db: Session,
    user_id: str,
    institution_id: str,
    required_roles: list[str] | None = None,
) -> InstitutionMembership:
    """Validate that the user has an active membership in the target institution."""
    query = select(InstitutionMembership).where(
        InstitutionMembership.user_id == user_id,
        InstitutionMembership.institution_id == institution_id,
    )
    membership = db.execute(query).scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this institution workspace.",
        )
    if membership.status != MembershipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Your membership is currently '{membership.status}'."
                " Active membership is required."
            ),
        )
    if required_roles and membership.role not in required_roles:
        # Check if platform admin override applies
        user = db.get(User, user_id)
        if not (user and user.is_superuser):
            roles_str = ", ".join(required_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This operation requires one of the following roles: {roles_str}.",
            )
    return membership


# ---------------------------------------------------------------------------
# Student Profile Operations
# ---------------------------------------------------------------------------


def get_student_profile(
    db: Session,
    user_id: str,
    institution_id: str,
) -> StudentProfile | None:
    """Retrieve the student profile for a user in an institution."""
    query = select(StudentProfile).where(
        StudentProfile.user_id == user_id,
        StudentProfile.institution_id == institution_id,
    )
    return db.execute(query).scalar_one_or_none()


def create_student_profile(
    db: Session,
    user_id: str,
    institution_id: str,
    data: StudentProfileCreate,
) -> StudentProfile:
    """Create a student profile for the authenticated user."""
    membership = _ensure_active_membership(db, user_id, institution_id)

    existing = get_student_profile(db, user_id, institution_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student profile already exists for this institution workspace.",
        )

    profile = StudentProfile(
        user_id=user_id,
        institution_id=institution_id,
        membership_id=membership.id,
        display_name=data.display_name,
        skills=data.skills,
        interests=data.interests,
        career_goals=data.career_goals,
        preferred_opportunity_types=data.preferred_opportunity_types,
        location_preference=data.location_preference,
        visibility=data.visibility,
        extra_data=data.extra_data,
    )
    db.add(profile)
    db.flush()
    return profile


def update_student_profile(
    db: Session,
    user_id: str,
    institution_id: str,
    data: StudentProfileUpdate,
) -> StudentProfile:
    """Update permitted fields on the student profile."""
    _ensure_active_membership(db, user_id, institution_id)

    profile = get_student_profile(db, user_id, institution_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Please create one first.",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    db.flush()
    return profile


# ---------------------------------------------------------------------------
# Alumni Profile Operations
# ---------------------------------------------------------------------------


def get_alumni_profile(
    db: Session,
    user_id: str,
    institution_id: str,
) -> AlumniProfile | None:
    """Retrieve the alumni profile for a user in an institution."""
    query = select(AlumniProfile).where(
        AlumniProfile.user_id == user_id,
        AlumniProfile.institution_id == institution_id,
    )
    return db.execute(query).scalar_one_or_none()


def create_alumni_profile(
    db: Session,
    user_id: str,
    institution_id: str,
    data: AlumniProfileCreate,
) -> AlumniProfile:
    """Create an alumni profile for the authenticated user."""
    membership = _ensure_active_membership(
        db,
        user_id,
        institution_id,
        required_roles=[
            InstitutionRole.ALUMNI.value,
            InstitutionRole.FACULTY.value,
            InstitutionRole.INSTITUTION_ADMIN.value,
            InstitutionRole.PLATFORM_ADMIN.value,
        ],
    )

    existing = get_alumni_profile(db, user_id, institution_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An alumni profile already exists for this institution workspace.",
        )

    profile = AlumniProfile(
        user_id=user_id,
        institution_id=institution_id,
        membership_id=membership.id,
        display_name=data.display_name,
        professional_domain=data.professional_domain,
        skills=data.skills,
        industry=data.industry,
        years_experience=data.years_experience,
        mentoring_interests=data.mentoring_interests,
        willing_to_connect=data.willing_to_connect,
        monthly_connection_limit=data.monthly_connection_limit,
        visibility=data.visibility,
        extra_data=data.extra_data,
    )
    db.add(profile)
    db.flush()
    return profile


def update_alumni_profile(
    db: Session,
    user_id: str,
    institution_id: str,
    data: AlumniProfileUpdate,
) -> AlumniProfile:
    """Update permitted fields on the alumni profile."""
    _ensure_active_membership(db, user_id, institution_id)

    profile = get_alumni_profile(db, user_id, institution_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumni profile not found. Please create one first.",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    db.flush()
    return profile


# ---------------------------------------------------------------------------
# Privacy-Aware Member Discovery
# ---------------------------------------------------------------------------


def discover_members(
    db: Session,
    institution_id: str,
    current_user: User,
    search: str | None = None,
    role_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[MemberDiscoveryRead], int]:
    """Discover members of an institution with strict server-side privacy enforcement."""
    # Ensure viewer has active membership in this institution
    viewer_membership = _ensure_active_membership(db, current_user.id, institution_id)
    viewer_role = viewer_membership.role
    is_admin = current_user.is_superuser or viewer_role in {
        InstitutionRole.PLATFORM_ADMIN.value,
        InstitutionRole.INSTITUTION_ADMIN.value,
    }

    # Query active memberships in the institution
    stmt = (
        select(InstitutionMembership)
        .options(
            joinedload(InstitutionMembership.user),
        )
        .where(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.status == MembershipStatus.ACTIVE.value,
        )
    )

    if role_filter:
        stmt = stmt.where(InstitutionMembership.role == role_filter)

    all_members = db.execute(stmt).scalars().all()

    # Preload positions for this institution
    pos_stmt = (
        select(CampusRoleAssignment)
        .where(
            CampusRoleAssignment.institution_id == institution_id,
            CampusRoleAssignment.is_active.is_(True),
        )
        .options(joinedload(CampusRoleAssignment.position))
    )
    positions = db.execute(pos_stmt).scalars().all()
    user_positions: dict[str, list[str]] = {}
    for assign in positions:
        if assign.user_id:
            title = assign.position.title if assign.position else "Campus Position"
            user_positions.setdefault(assign.user_id, []).append(title)

    # Preload active help offers count
    offer_stmt = select(HelpOffer).where(
        HelpOffer.institution_id == institution_id,
        HelpOffer.status == HelpOfferStatus.ACTIVE.value,
        HelpOffer.willing_to_help.is_(True),
    )
    offers = db.execute(offer_stmt).scalars().all()
    user_offers_count: dict[str, int] = {}
    for o in offers:
        user_offers_count[o.user_id] = user_offers_count.get(o.user_id, 0) + 1

    # Preload student & alumni profiles
    sp_stmt = select(StudentProfile).where(StudentProfile.institution_id == institution_id)
    student_profiles_map = {
        sp.user_id: sp for sp in db.execute(sp_stmt).scalars().all() if sp.user_id
    }

    ap_stmt = select(AlumniProfile).where(AlumniProfile.institution_id == institution_id)
    alumni_profiles_map = {
        ap.user_id: ap for ap in db.execute(ap_stmt).scalars().all() if ap.user_id
    }

    results: list[MemberDiscoveryRead] = []

    for m in all_members:
        u = m.user
        if not u or not u.is_active:
            continue

        is_self = u.id == current_user.id

        # Student profile projection
        sp = student_profiles_map.get(u.id)
        visible_sp: StudentProfileRead | None = None
        if sp:
            can_see_sp = False
            if is_self or is_admin or sp.visibility == StudentVisibility.PUBLIC:
                can_see_sp = True
            elif sp.visibility == StudentVisibility.ALUMNI_ONLY:
                can_see_sp = viewer_role in {
                    InstitutionRole.ALUMNI.value,
                    InstitutionRole.FACULTY.value,
                    InstitutionRole.INSTITUTION_ADMIN.value,
                }
            if can_see_sp:
                visible_sp = StudentProfileRead.model_validate(sp)

        # Alumni profile projection
        ap = alumni_profiles_map.get(u.id)
        visible_ap: AlumniProfileRead | None = None
        if ap:
            can_see_ap = False
            if is_self or is_admin or ap.visibility == AlumniVisibility.PUBLIC:
                can_see_ap = True
            elif ap.visibility == AlumniVisibility.STUDENTS_ONLY:
                can_see_ap = viewer_role in {
                    InstitutionRole.STUDENT.value,
                    InstitutionRole.FACULTY.value,
                    InstitutionRole.INSTITUTION_ADMIN.value,
                }
            if can_see_ap:
                visible_ap = AlumniProfileRead.model_validate(ap)

        # Apply search keyword filter if provided
        if search:
            q = search.lower()
            name_match = q in u.full_name.lower()
            sp_match = False
            if visible_sp:
                sp_match = any(
                    q in str(getattr(visible_sp, field, "")).lower()
                    for field in [
                        "skills",
                        "interests",
                        "career_goals",
                        "preferred_opportunity_types",
                    ]
                    if getattr(visible_sp, field, None)
                )
            ap_match = False
            if visible_ap:
                ap_match = any(
                    q in str(getattr(visible_ap, field, "")).lower()
                    for field in [
                        "skills",
                        "industry",
                        "professional_domain",
                        "mentoring_interests",
                    ]
                    if getattr(visible_ap, field, None)
                )
            if not (name_match or sp_match or ap_match):
                continue

        results.append(
            MemberDiscoveryRead(
                user_id=u.id,
                institution_id=institution_id,
                full_name=u.full_name,
                role=m.role,
                membership_status=m.status,
                student_profile=visible_sp,
                alumni_profile=visible_ap,
                active_help_offers_count=user_offers_count.get(u.id, 0),
                official_positions=user_positions.get(u.id, []),
            )
        )

    total = len(results)
    paginated = results[offset : offset + limit]
    return paginated, total
