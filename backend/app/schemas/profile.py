"""Schemas for StudentProfile, AlumniProfile, and Member Discovery.

These schemas define the validated input/output contracts for profile endpoints.
All profile data is self-reported and is not independently verified by the platform.
Schemas must not add fields that imply verification status.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.alumni_profile import ProfileVisibility as AlumniProfileVisibility
from app.models.student_profile import ProfileVisibility as StudentProfileVisibility


class StudentProfileCreate(BaseModel):
    """Input schema for creating a student profile."""

    display_name: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    interests: str | None = None
    career_goals: str | None = None
    preferred_opportunity_types: str | None = None
    location_preference: str | None = None
    visibility: StudentProfileVisibility = StudentProfileVisibility.PRIVATE
    extra_data: dict[str, Any] | None = None


class StudentProfileUpdate(BaseModel):
    """Input schema for updating an existing student profile."""

    display_name: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    interests: str | None = None
    career_goals: str | None = None
    preferred_opportunity_types: str | None = None
    location_preference: str | None = None
    visibility: StudentProfileVisibility | None = None
    extra_data: dict[str, Any] | None = None


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None = None
    institution_id: str | None = None
    membership_id: str | None = None
    display_name: str | None
    skills: str | None
    interests: str | None
    career_goals: str | None
    preferred_opportunity_types: str | None
    location_preference: str | None
    visibility: StudentProfileVisibility
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class AlumniProfileCreate(BaseModel):
    """Input schema for creating an alumni profile.

    All descriptive fields are optional. ``willing_to_connect`` must be
    explicitly set to True before the profile can receive connection requests.
    """

    display_name: str | None = Field(default=None, max_length=200)
    professional_domain: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    industry: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=70)
    mentoring_interests: str | None = None
    willing_to_connect: bool = False
    monthly_connection_limit: int | None = Field(default=None, ge=1, le=500)
    visibility: AlumniProfileVisibility = AlumniProfileVisibility.PRIVATE
    extra_data: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _limit_requires_connection(self) -> AlumniProfileCreate:
        if self.monthly_connection_limit is not None and not self.willing_to_connect:
            raise ValueError(
                "monthly_connection_limit is only meaningful when willing_to_connect is True"
            )
        return self


class AlumniProfileUpdate(BaseModel):
    """Input schema for updating an existing alumni profile."""

    display_name: str | None = Field(default=None, max_length=200)
    professional_domain: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    industry: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=70)
    mentoring_interests: str | None = None
    willing_to_connect: bool | None = None
    monthly_connection_limit: int | None = Field(default=None, ge=1, le=500)
    visibility: AlumniProfileVisibility | None = None
    extra_data: dict[str, Any] | None = None


class AlumniProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None = None
    institution_id: str | None = None
    membership_id: str | None = None
    display_name: str | None
    professional_domain: str | None
    skills: str | None
    industry: str | None
    years_experience: int | None
    mentoring_interests: str | None
    willing_to_connect: bool
    monthly_connection_limit: int | None
    visibility: AlumniProfileVisibility
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class MemberDiscoveryRead(BaseModel):
    """Sanitized public projection of an institution member."""

    user_id: str
    institution_id: str
    full_name: str
    role: str
    membership_status: str
    student_profile: StudentProfileRead | None = None
    alumni_profile: AlumniProfileRead | None = None
    active_help_offers_count: int = 0
    official_positions: list[str] = Field(default_factory=list)
