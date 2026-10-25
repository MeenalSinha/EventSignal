"""API endpoints for StudentProfile, AlumniProfile, and Member Discovery."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.alumni_profile import ProfileVisibility as AlumniProfileVisibility
from app.models.student_profile import ProfileVisibility as StudentProfileVisibility
from app.models.user import User
from app.schemas.profile import (
    AlumniProfileCreate,
    AlumniProfileRead,
    AlumniProfileUpdate,
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
)
from app.services import profile as profile_service

router = APIRouter(prefix="/institutions/{institution_id}/profiles", tags=["profiles"])


# ---------------------------------------------------------------------------
# Student Profile Endpoints
# ---------------------------------------------------------------------------


@router.get("/student/me", response_model=StudentProfileRead)
def get_my_student_profile(
    institution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudentProfileRead:
    """Retrieve the authenticated user's own student profile in this institution."""
    profile = profile_service.get_student_profile(db, current_user.id, institution_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile has not been created yet.",
        )
    return StudentProfileRead.model_validate(profile)


@router.post("/student", response_model=StudentProfileRead, status_code=status.HTTP_201_CREATED)
def create_my_student_profile(
    institution_id: str,
    data: StudentProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudentProfileRead:
    """Create a student profile for the authenticated user."""
    profile = profile_service.create_student_profile(db, current_user.id, institution_id, data)
    db.commit()
    db.refresh(profile)
    return StudentProfileRead.model_validate(profile)


@router.patch("/student", response_model=StudentProfileRead)
def update_my_student_profile(
    institution_id: str,
    data: StudentProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StudentProfileRead:
    """Update fields on the authenticated user's student profile."""
    profile = profile_service.update_student_profile(db, current_user.id, institution_id, data)
    db.commit()
    db.refresh(profile)
    return StudentProfileRead.model_validate(profile)


# ---------------------------------------------------------------------------
# Alumni Profile Endpoints
# ---------------------------------------------------------------------------


@router.get("/alumni/me", response_model=AlumniProfileRead)
def get_my_alumni_profile(
    institution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AlumniProfileRead:
    """Retrieve the authenticated user's own alumni profile in this institution."""
    profile = profile_service.get_alumni_profile(db, current_user.id, institution_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumni profile has not been created yet.",
        )
    return AlumniProfileRead.model_validate(profile)


@router.post("/alumni", response_model=AlumniProfileRead, status_code=status.HTTP_201_CREATED)
def create_my_alumni_profile(
    institution_id: str,
    data: AlumniProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AlumniProfileRead:
    """Create an alumni profile for the authenticated user."""
    profile = profile_service.create_alumni_profile(db, current_user.id, institution_id, data)
    db.commit()
    db.refresh(profile)
    return AlumniProfileRead.model_validate(profile)


@router.patch("/alumni", response_model=AlumniProfileRead)
def update_my_alumni_profile(
    institution_id: str,
    data: AlumniProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AlumniProfileRead:
    """Update fields on the authenticated user's alumni profile."""
    profile = profile_service.update_alumni_profile(db, current_user.id, institution_id, data)
    db.commit()
    db.refresh(profile)
    return AlumniProfileRead.model_validate(profile)


# ---------------------------------------------------------------------------
# Member Discovery Endpoints
# ---------------------------------------------------------------------------


@router.get("/members", response_model=dict[str, object])
def discover_institution_members(
    institution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    search: str | None = None,
    role: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    """Discover authorized members in the institution workspace with privacy rules."""
    items, total = profile_service.discover_members(
        db,
        institution_id=institution_id,
        current_user=current_user,
        search=search,
        role_filter=role,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ---------------------------------------------------------------------------
# Compatibility Routes for Frontend profileService (/profiles/...)
# ---------------------------------------------------------------------------

compat_router = APIRouter(prefix="/profiles", tags=["profiles-compat"])


@compat_router.get("/student/me", response_model=StudentProfileRead)
def get_my_student_profile_compat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    institution_id: str | None = None,
    x_institution_id: Annotated[str | None, Header(alias="X-Institution-Id")] = None,
) -> StudentProfileRead:
    inst_id = institution_id or x_institution_id
    if not inst_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id parameter or X-Institution-Id header is required",
        )
    profile = profile_service.get_student_profile(db, current_user.id, inst_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile has not been created yet.",
        )
    return StudentProfileRead.model_validate(profile)


@compat_router.post("/student", response_model=StudentProfileRead)
def save_my_student_profile_compat(
    data: dict[str, Any],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    institution_id: str | None = None,
    x_institution_id: Annotated[str | None, Header(alias="X-Institution-Id")] = None,
) -> StudentProfileRead:
    inst_id = institution_id or x_institution_id
    if not inst_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id parameter or X-Institution-Id header is required",
        )

    skills_raw = data.get("skills")
    skills_val = ", ".join(skills_raw) if isinstance(skills_raw, list) else skills_raw
    interests_raw = data.get("interests")
    interests_val = ", ".join(interests_raw) if isinstance(interests_raw, list) else interests_raw
    goals_raw = data.get("career_goals")
    goals_val = ", ".join(goals_raw) if isinstance(goals_raw, list) else goals_raw
    vis_val = data.get("visibility")
    if isinstance(vis_val, StudentProfileVisibility):
        vis = vis_val
    elif vis_val == "alumni_only":
        vis = StudentProfileVisibility.ALUMNI_ONLY
    elif vis_val == "private":
        vis = StudentProfileVisibility.PRIVATE
    elif vis_val in ("public", "institution_only") or not vis_val:
        vis = StudentProfileVisibility.PUBLIC
    else:
        try:
            vis = StudentProfileVisibility(str(vis_val))
        except ValueError:
            vis = StudentProfileVisibility.PRIVATE
    extra = {
        "headline": data.get("headline"),
        "bio": data.get("bio"),
        "degree_level": data.get("degree_level"),
        "graduation_year": data.get("graduation_year"),
    }

    existing = profile_service.get_student_profile(db, current_user.id, inst_id)
    if existing:
        update_data = StudentProfileUpdate(
            display_name=data.get("headline") or existing.display_name,
            skills=skills_val,
            interests=interests_val,
            career_goals=goals_val,
            visibility=vis,
            extra_data=extra,
        )
        profile = profile_service.update_student_profile(db, current_user.id, inst_id, update_data)
    else:
        create_data = StudentProfileCreate(
            display_name=data.get("headline"),
            skills=skills_val,
            interests=interests_val,
            career_goals=goals_val,
            visibility=vis,
            extra_data=extra,
        )
        profile = profile_service.create_student_profile(db, current_user.id, inst_id, create_data)

    db.commit()
    db.refresh(profile)
    return StudentProfileRead.model_validate(profile)


@compat_router.get("/alumni/me", response_model=AlumniProfileRead)
def get_my_alumni_profile_compat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    institution_id: str | None = None,
    x_institution_id: Annotated[str | None, Header(alias="X-Institution-Id")] = None,
) -> AlumniProfileRead:
    inst_id = institution_id or x_institution_id
    if not inst_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id parameter or X-Institution-Id header is required",
        )
    profile = profile_service.get_alumni_profile(db, current_user.id, inst_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alumni profile has not been created yet.",
        )
    return AlumniProfileRead.model_validate(profile)


@compat_router.post("/alumni", response_model=AlumniProfileRead)
def save_my_alumni_profile_compat(
    data: dict[str, Any],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    institution_id: str | None = None,
    x_institution_id: Annotated[str | None, Header(alias="X-Institution-Id")] = None,
) -> AlumniProfileRead:
    inst_id = institution_id or x_institution_id
    if not inst_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id parameter or X-Institution-Id header is required",
        )

    skills_raw = data.get("skills")
    skills_val = ", ".join(skills_raw) if isinstance(skills_raw, list) else skills_raw
    topics_raw = data.get("mentoring_topics")
    topics_val = ", ".join(topics_raw) if isinstance(topics_raw, list) else topics_raw
    vis_val = data.get("visibility")
    if isinstance(vis_val, AlumniProfileVisibility):
        vis = vis_val
    elif vis_val in ("students_only", "institution_only"):
        vis = AlumniProfileVisibility.STUDENTS_ONLY
    elif vis_val == "public":
        vis = AlumniProfileVisibility.PUBLIC
    elif vis_val == "private":
        vis = AlumniProfileVisibility.PRIVATE
    elif not vis_val:
        vis = AlumniProfileVisibility.STUDENTS_ONLY
    else:
        try:
            vis = AlumniProfileVisibility(str(vis_val))
        except ValueError:
            vis = AlumniProfileVisibility.PRIVATE
    extra = {
        "current_title": data.get("current_title"),
        "current_organization": data.get("current_organization"),
        "bio": data.get("bio"),
    }

    existing = profile_service.get_alumni_profile(db, current_user.id, inst_id)
    if existing:
        update_data = AlumniProfileUpdate(
            display_name=data.get("current_title") or existing.display_name,
            professional_domain=data.get("professional_domain") or existing.professional_domain,
            industry=data.get("industry") or existing.industry,
            years_experience=data.get("years_of_experience") or existing.years_experience,
            skills=skills_val,
            mentoring_interests=topics_val,
            willing_to_connect=data.get("willing_to_help", True),
            monthly_connection_limit=data.get("monthly_request_limit", 5),
            visibility=vis,
            extra_data=extra,
        )
        profile = profile_service.update_alumni_profile(db, current_user.id, inst_id, update_data)
    else:
        create_data = AlumniProfileCreate(
            display_name=data.get("current_title"),
            professional_domain=data.get("professional_domain"),
            industry=data.get("industry"),
            years_experience=data.get("years_of_experience"),
            skills=skills_val,
            mentoring_interests=topics_val,
            willing_to_connect=data.get("willing_to_help", True),
            monthly_connection_limit=data.get("monthly_request_limit", 5),
            visibility=vis,
            extra_data=extra,
        )
        profile = profile_service.create_alumni_profile(db, current_user.id, inst_id, create_data)

    db.commit()
    db.refresh(profile)
    return AlumniProfileRead.model_validate(profile)


@compat_router.get("/discovery", response_model=list[dict[str, object]])
def discover_members_compat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    institution_id: str | None = None,
    x_institution_id: Annotated[str | None, Header(alias="X-Institution-Id")] = None,
    role: str | None = None,
    q: str | None = None,
) -> list[dict[str, object]]:
    inst_id = institution_id or x_institution_id
    if not inst_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="institution_id parameter or X-Institution-Id header is required",
        )
    items, _total = profile_service.discover_members(
        db,
        institution_id=inst_id,
        current_user=current_user,
        search=q,
        role_filter=role,
    )
    return [item.model_dump() for item in items]

