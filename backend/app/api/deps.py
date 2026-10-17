"""FastAPI authentication and RBAC dependency injectors."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database import get_db
from app.models.membership import InstitutionRole, MembershipStatus
from app.models.user import User
from app.services.auth import get_user_by_id, verify_user_token
from app.services.institution import get_member


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
    db: Annotated[Session, Depends(get_db)] = None,  # type: ignore[assignment]
) -> User:
    """Extract and validate the authenticated user from the Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format; expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    try:
        payload = verify_user_token(token, settings.auth_secret_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_optional_current_user(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
    db: Annotated[Session, Depends(get_db)] = None,  # type: ignore[assignment]
) -> User | None:
    """Optionally extract the authenticated user if Authorization header is provided."""
    if not authorization:
        return None
    try:
        return get_current_user(authorization=authorization, settings=settings, db=db)
    except HTTPException:
        return None


def require_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the user is a platform super administrator."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator privileges required",
        )
    return current_user


def require_institution_admin_access(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Ensure user is either a platform superuser or active institution admin."""
    if current_user.is_superuser:
        return current_user

    membership = get_member(db, institution_id, current_user.id)
    if (
        not membership
        or membership.status != MembershipStatus.ACTIVE
        or membership.role
        not in (InstitutionRole.INSTITUTION_ADMIN, InstitutionRole.PLATFORM_ADMIN)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institution administrator privileges required for this workspace",
        )
    return current_user


def require_institution_membership(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Ensure user has an active membership in the given college workspace."""
    if current_user.is_superuser:
        return current_user

    membership = get_member(db, institution_id, current_user.id)
    if not membership or membership.status != MembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active institutional membership required to access this workspace",
        )
    return current_user
