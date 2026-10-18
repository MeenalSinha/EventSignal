"""HelpOffer service: lifecycle, publishing, discovery, filtering, and connection requests."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.alumni_profile import AlumniProfile
from app.models.connection_request import ConnectionRequest, RequestStatus
from app.models.help_offer import (
    HelpOffer,
    HelpOfferAudience,
    HelpOfferStatus,
)
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.student_profile import ProfileVisibility as StudentVisibility
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.connection import HelpOfferRequestCreate
from app.schemas.help_offer import (
    HelpOfferCreate,
    HelpOfferListResponse,
    HelpOfferRead,
    HelpOfferUpdate,
)
from app.services.audit import log_audit_event


def _ensure_active_membership(
    db: Session,
    user_id: str,
    institution_id: str,
) -> InstitutionMembership:
    query = select(InstitutionMembership).where(
        InstitutionMembership.user_id == user_id,
        InstitutionMembership.institution_id == institution_id,
    )
    membership = db.execute(query).scalar_one_or_none()
    if not membership or membership.status != MembershipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active institution membership is required.",
        )
    return membership


def create_help_offer(
    db: Session,
    user_id: str,
    institution_id: str,
    data: HelpOfferCreate,
) -> HelpOfferRead:
    """Create and publish a new help offer."""
    membership = _ensure_active_membership(db, user_id, institution_id)

    offer = HelpOffer(
        user_id=user_id,
        institution_id=institution_id,
        membership_id=membership.id,
        title=data.title,
        category=data.category.strip().lower(),
        description=data.description,
        applicable_skills=data.applicable_skills,
        intended_audience=data.intended_audience,
        delivery_mode=data.delivery_mode,
        availability_description=data.availability_description,
        status=HelpOfferStatus.ACTIVE.value,
        willing_to_help=data.willing_to_help,
        extra_data=data.extra_data,
    )
    db.add(offer)
    db.flush()

    user = db.get(User, user_id)
    log_audit_event(
        db,
        action="create_help_offer",
        target_type="help_offer",
        target_id=offer.id,
        institution_id=institution_id,
        actor_user_id=user_id,
        details={"title": offer.title, "category": offer.category},
    )

    result = HelpOfferRead.model_validate(offer)
    result.owner_name = user.full_name if user else None
    result.owner_role = membership.role
    return result


def list_my_help_offers(
    db: Session,
    user_id: str,
    institution_id: str,
) -> list[HelpOfferRead]:
    """Retrieve all help offers created by the authenticated user in this workspace."""
    _ensure_active_membership(db, user_id, institution_id)

    stmt = (
        select(HelpOffer)
        .options(joinedload(HelpOffer.user))
        .where(
            HelpOffer.user_id == user_id,
            HelpOffer.institution_id == institution_id,
        )
        .order_by(HelpOffer.created_at.desc())
    )
    offers = db.execute(stmt).scalars().all()
    user = db.get(User, user_id)

    results: list[HelpOfferRead] = []
    for o in offers:
        item = HelpOfferRead.model_validate(o)
        item.owner_name = user.full_name if user else None
        results.append(item)
    return results


def get_help_offer(
    db: Session,
    offer_id: str,
    current_user: User,
) -> HelpOfferRead:
    """Retrieve details of a single help offer."""
    offer = db.get(HelpOffer, offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help offer not found.",
        )

    # Tenant boundary
    membership = _ensure_active_membership(db, current_user.id, offer.institution_id)

    is_owner = offer.user_id == current_user.id
    is_admin = current_user.is_superuser or membership.role in {
        InstitutionRole.PLATFORM_ADMIN.value,
        InstitutionRole.INSTITUTION_ADMIN.value,
    }

    if offer.status != HelpOfferStatus.ACTIVE.value and not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help offer is currently unavailable.",
        )

    owner = db.get(User, offer.user_id)
    owner_membership = db.execute(
        select(InstitutionMembership).where(
            InstitutionMembership.user_id == offer.user_id,
            InstitutionMembership.institution_id == offer.institution_id,
        )
    ).scalar_one_or_none()

    item = HelpOfferRead.model_validate(offer)
    item.owner_name = owner.full_name if owner else None
    item.owner_role = owner_membership.role if owner_membership else None
    return item


def update_help_offer(
    db: Session,
    offer_id: str,
    user_id: str,
    data: HelpOfferUpdate,
) -> HelpOfferRead:
    """Update or toggle status/consent on an existing help offer."""
    offer = db.get(HelpOffer, offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help offer not found.",
        )

    membership = _ensure_active_membership(db, user_id, offer.institution_id)
    is_owner = offer.user_id == user_id
    user = db.get(User, user_id)
    is_admin = bool(user and user.is_superuser) or membership.role in {
        InstitutionRole.PLATFORM_ADMIN.value,
        InstitutionRole.INSTITUTION_ADMIN.value,
    }

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this help offer.",
        )

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "category" and isinstance(value, str):
            setattr(offer, field, value.strip().lower())
        else:
            setattr(offer, field, value)

    db.add(offer)
    db.flush()

    log_audit_event(
        db,
        action="update_help_offer",
        target_type="help_offer",
        target_id=offer.id,
        institution_id=offer.institution_id,
        actor_user_id=user_id,
        details=update_dict,
    )

    owner = db.get(User, offer.user_id)
    result = HelpOfferRead.model_validate(offer)
    result.owner_name = owner.full_name if owner else None
    result.owner_role = membership.role
    return result


def archive_help_offer(
    db: Session,
    offer_id: str,
    user_id: str,
) -> None:
    """Archive a help offer so it is removed from active discovery."""
    offer = db.get(HelpOffer, offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help offer not found.",
        )

    membership = _ensure_active_membership(db, user_id, offer.institution_id)
    is_owner = offer.user_id == user_id
    user = db.get(User, user_id)
    is_admin = bool(user and user.is_superuser) or membership.role in {
        InstitutionRole.PLATFORM_ADMIN.value,
        InstitutionRole.INSTITUTION_ADMIN.value,
    }

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to archive this help offer.",
        )

    offer.status = HelpOfferStatus.ARCHIVED.value
    offer.willing_to_help = False
    db.add(offer)
    db.flush()

    log_audit_event(
        db,
        action="archive_help_offer",
        target_type="help_offer",
        target_id=offer.id,
        institution_id=offer.institution_id,
        actor_user_id=user_id,
    )


def discover_help_offers(
    db: Session,
    institution_id: str,
    current_user: User,
    category: str | None = None,
    search: str | None = None,
    delivery_mode: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> HelpOfferListResponse:
    """Discover active help offers within an authorized institution community."""
    viewer_membership = _ensure_active_membership(db, current_user.id, institution_id)
    viewer_role = viewer_membership.role

    stmt = (
        select(HelpOffer)
        .options(joinedload(HelpOffer.user))
        .where(
            HelpOffer.institution_id == institution_id,
            HelpOffer.status == HelpOfferStatus.ACTIVE.value,
            HelpOffer.willing_to_help.is_(True),
        )
    )

    if category:
        stmt = stmt.where(HelpOffer.category == category.strip().lower())
    if delivery_mode:
        stmt = stmt.where(HelpOffer.delivery_mode == delivery_mode)

    all_offers = db.execute(stmt.order_by(HelpOffer.created_at.desc())).scalars().all()

    # Preload memberships for owner role annotations
    owner_ids = [o.user_id for o in all_offers]
    owner_memberships: dict[str, str] = {}
    if owner_ids:
        mem_stmt = select(InstitutionMembership).where(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.user_id.in_(owner_ids),
        )
        for mem in db.execute(mem_stmt).scalars().all():
            owner_memberships[mem.user_id] = mem.role

    filtered_items: list[HelpOfferRead] = []
    for offer in all_offers:
        # Check intended audience
        if offer.intended_audience == HelpOfferAudience.STUDENTS_ONLY.value and viewer_role not in {
            InstitutionRole.STUDENT.value,
            InstitutionRole.FACULTY.value,
            InstitutionRole.INSTITUTION_ADMIN.value,
            InstitutionRole.PLATFORM_ADMIN.value,
        }:
            continue
        if offer.intended_audience == HelpOfferAudience.ALUMNI_ONLY.value and viewer_role not in {
            InstitutionRole.ALUMNI.value,
            InstitutionRole.FACULTY.value,
            InstitutionRole.INSTITUTION_ADMIN.value,
            InstitutionRole.PLATFORM_ADMIN.value,
        }:
            continue

        # Check search query across title, description, and applicable_skills
        if search:
            q = search.lower()
            in_title = q in offer.title.lower()
            in_desc = q in offer.description.lower()
            in_skills = bool(offer.applicable_skills and q in offer.applicable_skills.lower())
            owner_name = offer.user.full_name if offer.user else ""
            in_name = q in owner_name.lower()
            if not (in_title or in_desc or in_skills or in_name):
                continue

        item = HelpOfferRead.model_validate(offer)
        item.owner_name = offer.user.full_name if offer.user else None
        item.owner_role = owner_memberships.get(offer.user_id)
        filtered_items.append(item)

    total = len(filtered_items)
    paginated = filtered_items[offset : offset + limit]
    distinct_categories = sorted({o.category for o in all_offers if o.category})
    return HelpOfferListResponse(
        items=paginated,
        total=total,
        limit=limit,
        offset=offset,
        categories=distinct_categories,
    )


# ---------------------------------------------------------------------------
# Purpose-Specific Requests to Published Help Offers
# ---------------------------------------------------------------------------


def create_help_offer_request(
    db: Session,
    offer_id: str,
    current_user: User,
    data: HelpOfferRequestCreate,
) -> ConnectionRequest:
    """Submit a purpose-specific request on an active published help offer."""
    offer = db.get(HelpOffer, offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help offer not found.",
        )

    # Active membership check
    _ensure_active_membership(db, current_user.id, offer.institution_id)

    # Offer status & consent check
    if offer.status != HelpOfferStatus.ACTIVE.value or not offer.willing_to_help:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This help offer is currently not accepting requests.",
        )

    # Anti-self-request check
    if offer.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot request assistance from your own help offer.",
        )

    # Requester student profile (get or initialize minimal)
    student_profile = db.execute(
        select(StudentProfile).where(
            StudentProfile.user_id == current_user.id,
            StudentProfile.institution_id == offer.institution_id,
        )
    ).scalar_one_or_none()

    if not student_profile:
        student_profile = StudentProfile(
            user_id=current_user.id,
            institution_id=offer.institution_id,
            display_name=current_user.full_name,
            visibility=StudentVisibility.PUBLIC,
        )
        db.add(student_profile)
        db.flush()

    # Recipient alumni profile (get or initialize minimal)
    alumni_profile = db.execute(
        select(AlumniProfile).where(
            AlumniProfile.user_id == offer.user_id,
            AlumniProfile.institution_id == offer.institution_id,
        )
    ).scalar_one_or_none()

    if not alumni_profile:
        owner_user = db.get(User, offer.user_id)
        alumni_profile = AlumniProfile(
            user_id=offer.user_id,
            institution_id=offer.institution_id,
            display_name=owner_user.full_name if owner_user else "Alumnus / Mentor",
            willing_to_connect=True,
        )
        db.add(alumni_profile)
        db.flush()

    # Prevent duplicate pending requests for the same offer
    existing_req = db.execute(
        select(ConnectionRequest).where(
            ConnectionRequest.requester_profile_id == student_profile.id,
            ConnectionRequest.recipient_profile_id == alumni_profile.id,
            ConnectionRequest.help_offer_id == offer.id,
            ConnectionRequest.status == RequestStatus.PENDING,
        )
    ).scalar_one_or_none()

    if existing_req:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending request for this help offer.",
        )

    req = ConnectionRequest(
        requester_profile_id=student_profile.id,
        recipient_profile_id=alumni_profile.id,
        help_offer_id=offer.id,
        purpose=data.purpose,
        message=data.message,
        status=RequestStatus.PENDING,
    )
    db.add(req)
    db.flush()

    log_audit_event(
        db,
        action="send_help_offer_request",
        target_type="connection_request",
        target_id=req.id,
        institution_id=offer.institution_id,
        actor_user_id=current_user.id,
        details={"offer_id": offer.id, "purpose": data.purpose.value},
    )

    return req


def list_offer_requests(
    db: Session,
    offer_id: str,
    current_user: User,
) -> list[ConnectionRequest]:
    """List incoming requests on a help offer (accessible to offer owner or admin)."""
    offer = db.get(HelpOffer, offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help offer not found.",
        )

    membership = _ensure_active_membership(db, current_user.id, offer.institution_id)
    is_owner = offer.user_id == current_user.id
    is_admin = current_user.is_superuser or membership.role in {
        InstitutionRole.PLATFORM_ADMIN.value,
        InstitutionRole.INSTITUTION_ADMIN.value,
    }

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view requests for this offer.",
        )

    stmt = (
        select(ConnectionRequest)
        .where(ConnectionRequest.help_offer_id == offer_id)
        .order_by(ConnectionRequest.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
