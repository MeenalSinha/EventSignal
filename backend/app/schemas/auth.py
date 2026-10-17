"""Pydantic schemas for user identity and authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Payload for registering a new user."""

    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Payload for logging into an existing account."""

    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Bearer token returned upon successful authentication."""

    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int


class UserResponse(BaseModel):
    """Public user profile information."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    extra_data: dict[str, Any] | None = None


class UserProfileResponse(BaseModel):
    """Authenticated user info bundled with memberships."""

    user: UserResponse
    memberships: list[dict[str, Any]]
