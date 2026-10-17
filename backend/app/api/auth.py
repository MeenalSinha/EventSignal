"""Authentication and user profile endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
    UserResponse,
)
from app.services.auth import (
    AuthenticationError,
    UserAlreadyExistsError,
    authenticate_user,
    create_user_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Register a new user account and return a bearer access token."""
    try:
        user = register_user(
            session=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    db.commit()
    db.refresh(user)

    token, expires_in = create_user_token(user, settings)
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in_seconds=expires_in,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log into an existing user account",
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Verify credentials and return a bearer access token."""
    try:
        user = authenticate_user(
            session=db,
            email=payload.email,
            password=payload.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token, expires_in = create_user_token(user, settings)
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in_seconds=expires_in,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user details and institutional memberships",
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserProfileResponse:
    """Return profile and all affiliated college memberships for the authenticated user."""
    memberships_data = [
        {
            "id": m.id,
            "institution_id": m.institution_id,
            "institution_name": m.institution.name if m.institution else None,
            "institution_slug": m.institution.slug if m.institution else None,
            "role": m.role.value,
            "status": m.status.value,
            "joined_at": m.joined_at.isoformat(),
        }
        for m in current_user.memberships
    ]

    return UserProfileResponse(
        user=UserResponse.model_validate(current_user),
        memberships=memberships_data,
    )
