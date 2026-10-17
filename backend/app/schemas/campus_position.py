"""Pydantic schemas for campus position definitions and official role assignments."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.campus_position import AssignmentVerificationStatus


class PositionCreate(BaseModel):
    """Payload to define an official campus position."""

    title: str = Field(min_length=2, max_length=200)
    unit_id: str | None = None
    description: str | None = None
    is_leadership: bool = False


class PositionUpdate(BaseModel):
    """Payload to update an official campus position."""

    title: str | None = Field(default=None, min_length=2, max_length=200)
    unit_id: str | None = None
    description: str | None = None
    is_leadership: bool | None = None


class PositionResponse(BaseModel):
    """Details of a campus position definition."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    unit_id: str | None
    title: str
    description: str | None
    is_leadership: bool
    created_at: datetime
    updated_at: datetime


class AssignmentCreate(BaseModel):
    """Payload to appoint a user to a campus position."""

    user_id: str
    position_id: str
    unit_id: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    is_active: bool = True


class AssignmentUpdate(BaseModel):
    """Payload to update an assignment's tenure or active status."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None


class AssignmentVerifyRequest(BaseModel):
    """Payload for campus authority to verify or reject an appointment."""

    verification_status: AssignmentVerificationStatus  # VERIFIED or REJECTED


class AssignmentResponse(BaseModel):
    """Details of an official campus role assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    user_id: str
    position_id: str
    unit_id: str | None
    start_date: datetime
    end_date: datetime | None
    is_active: bool
    verification_status: AssignmentVerificationStatus
    verified_at: datetime | None
    verified_by_user_id: str | None
    created_at: datetime
    updated_at: datetime
    user_full_name: str | None = None
    user_email: str | None = None
    position_title: str | None = None
    unit_name: str | None = None
