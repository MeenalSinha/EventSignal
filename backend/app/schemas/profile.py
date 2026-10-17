"""Schemas for StudentProfile and AlumniProfile.

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
    """Input schema for creating or updating a student profile.

    All fields are optional because students may fill in their profile incrementally.
    """

    display_name: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    interests: str | None = None
    career_goals: str | None = None
    preferred_opportunity_types: str | None = None
    location_preference: str | None = None
    visibility: StudentProfileVisibility = StudentProfileVisibility.PRIVATE
    extra_data: dict[str, Any] | None = None


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str | None
    skills: str | None
    interests: str | None
    career_goals: str | None
    preferred_opportunity_types: str | None
    location_preference: str | None
    visibility: StudentProfileVisibility
    created_at: datetime
    updated_at: datetime


class AlumniProfileCreate(BaseModel):
    """Input schema for creating or updating an alumni profile.

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


class AlumniProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str | None
    professional_domain: str | None
    skills: str | None
    industry: str | None
    years_experience: int | None
    mentoring_interests: str | None
    willing_to_connect: bool
    monthly_connection_limit: int | None
    visibility: AlumniProfileVisibility
    created_at: datetime
    updated_at: datetime
