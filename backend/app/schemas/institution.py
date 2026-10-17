"""Pydantic schemas for institutions and college workspaces."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.institution import InstitutionStatus, InstitutionVerificationStatus


class InstitutionCreate(BaseModel):
    """Payload for registering a new college workspace."""

    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    domain: str | None = Field(default=None, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    website_url: str | None = Field(default=None, max_length=1024)
    extra_data: dict[str, Any] | None = None


class InstitutionUpdate(BaseModel):
    """Payload for updating institution metadata."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    domain: str | None = Field(default=None, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    website_url: str | None = Field(default=None, max_length=1024)
    status: InstitutionStatus | None = None
    verification_status: InstitutionVerificationStatus | None = None
    extra_data: dict[str, Any] | None = None


class InstitutionResponse(BaseModel):
    """Details of an institution workspace."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    domain: str | None
    description: str | None
    location: str | None
    contact_email: str | None
    website_url: str | None
    status: InstitutionStatus
    verification_status: InstitutionVerificationStatus
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    extra_data: dict[str, Any] | None = None


class InstitutionWorkspaceSummary(BaseModel):
    """Aggregated institutional workspace statistics and highlights."""

    institution: InstitutionResponse
    total_members: int
    total_units: int
    total_positions: int
    active_assignments: int
    total_opportunities: int
