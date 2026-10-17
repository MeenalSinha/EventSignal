"""User registration, authentication, and token management service."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthenticationError(ValueError):
    """Raised when authentication credentials fail."""


class UserAlreadyExistsError(ValueError):
    """Raised when registering an email that is already taken."""


def register_user(
    session: Session,
    email: str,
    password: str,
    full_name: str,
    is_superuser: bool = False,
    extra_data: dict[str, Any] | None = None,
) -> User:
    """Register a new user account."""
    clean_email = email.strip().lower()
    existing = session.scalar(select(User).where(User.email == clean_email))
    if existing:
        raise UserAlreadyExistsError(f"User with email '{clean_email}' already exists")

    hashed = hash_password(password)
    user = User(
        email=clean_email,
        hashed_password=hashed,
        full_name=full_name.strip(),
        is_active=True,
        is_superuser=is_superuser,
        extra_data=extra_data,
    )
    session.add(user)
    session.flush()
    return user


def authenticate_user(session: Session, email: str, password: str) -> User:
    """Authenticate email and password."""
    clean_email = email.strip().lower()
    user = session.scalar(select(User).where(User.email == clean_email))
    if not user:
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise AuthenticationError("User account is inactive")
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    return user


def get_user_by_id(session: Session, user_id: str) -> User | None:
    """Look up user by ID."""
    return session.get(User, user_id)


def get_user_by_email(session: Session, email: str) -> User | None:
    """Look up user by email."""
    return session.scalar(select(User).where(User.email == email.strip().lower()))


def create_user_token(user: User, settings: Settings) -> tuple[str, int]:
    """Issue a signed bearer token for the user."""
    expires_in_seconds = settings.auth_token_expire_minutes * 60
    is_demo = bool(
        user.extra_data and user.extra_data.get("is_demo") is True
    )
    claims = {
        "email": user.email,
        "is_superuser": user.is_superuser,
        "is_demo": is_demo,
    }
    token = create_access_token(
        subject=user.id,
        secret_key=settings.auth_secret_key,
        expires_in_seconds=expires_in_seconds,
        claims=claims,
    )
    return token, expires_in_seconds


def verify_user_token(token: str, secret_key: str) -> dict[str, Any]:
    """Verify and decode a user bearer token."""
    return decode_access_token(token, secret_key)
