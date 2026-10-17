"""API endpoints for StudentProfile, AlumniProfile, and Member Discovery."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
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
