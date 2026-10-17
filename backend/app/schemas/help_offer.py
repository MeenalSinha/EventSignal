"""Pydantic schemas for HelpOffer entity, management, and discovery."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HelpOfferCreate(BaseModel):
    """Payload for creating a new declared help offer."""

    title: str = Field(min_length=3, max_length=255)
    category: str = Field(
        min_length=2,
        max_length=64,
        description="Assistance category (e.g. portfolio_review, mock_interview, etc.)",
    )
    description: str = Field(
        min_length=5, description="Clear description of the assistance provided"
    )
    applicable_skills: str | None = Field(
        default=None, description="Keywords or skills applicable to this offer"
    )
    intended_audience: str = Field(
        default="all", description="'all', 'students_only', or 'alumni_only'"
    )
    delivery_mode: str = Field(
        default="remote", description="'remote', 'in_person', 'hybrid', or 'async'"
    )
    availability_description: str | None = Field(
        default=None,
        description="Declared general availability (e.g. '2 sessions/month on weekends')",
    )
    willing_to_help: bool = Field(
        default=True, description="Explicit owner consent to receive requests for this offer"
    )
    extra_data: dict[str, Any] | None = None


class HelpOfferUpdate(BaseModel):
    """Payload for updating an existing help offer."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = Field(default=None, min_length=5)
    applicable_skills: str | None = None
    intended_audience: str | None = None
    delivery_mode: str | None = None
    availability_description: str | None = None
    status: str | None = Field(
        default=None, description="'active', 'paused', 'archived', or 'draft'"
    )
    willing_to_help: bool | None = None
    extra_data: dict[str, Any] | None = None


class HelpOfferRead(BaseModel):
    """Read contract for a HelpOffer."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    institution_id: str
    membership_id: str | None = None
    title: str
    category: str
    description: str
    applicable_skills: str | None = None
    intended_audience: str
    delivery_mode: str
    availability_description: str | None = None
    status: str
    willing_to_help: bool
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    owner_name: str | None = None
    owner_role: str | None = None


class HelpOfferListResponse(BaseModel):
    """Paginated response of discoverable help offers."""

    items: list[HelpOfferRead]
    total: int
    limit: int
    offset: int
