"""Pydantic schemas for HelpOffer entity, management, and discovery."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    # Frontend compatibility aliases
    target_audience: str | None = None
    topics: list[str] = Field(default_factory=list)
    creator_name: str | None = None
    creator_role: str | None = None
    capacity_per_month: int = 5

    @model_validator(mode="after")
    def populate_frontend_aliases(self) -> HelpOfferRead:
        if not self.target_audience and self.intended_audience:
            self.target_audience = self.intended_audience
        if not self.creator_name and self.owner_name:
            self.creator_name = self.owner_name
        if not self.creator_role and self.owner_role:
            self.creator_role = self.owner_role
        if not self.topics and self.applicable_skills:
            self.topics = [s.strip() for s in self.applicable_skills.split(",") if s.strip()]
        if self.extra_data and "max_recipients" in self.extra_data:
            try:
                self.capacity_per_month = int(self.extra_data["max_recipients"])
            except (ValueError, TypeError):
                self.capacity_per_month = 5
        return self


class HelpOfferListResponse(BaseModel):
    """Paginated response of discoverable help offers."""

    items: list[HelpOfferRead]
    total: int
    limit: int
    offset: int
    categories: list[str] = Field(default_factory=list)
