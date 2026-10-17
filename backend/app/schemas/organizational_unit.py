"""Pydantic schemas for campus organizational units (departments, cells, offices)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UnitCreate(BaseModel):
    """Payload to create an organizational unit within an institution."""

    name: str = Field(min_length=2, max_length=200)
    code: str | None = Field(default=None, max_length=50)
    unit_type: str = Field(default="department", max_length=50)
    parent_id: str | None = None
    description: str | None = None
    contact_email: str | None = Field(default=None, max_length=255)


class UnitUpdate(BaseModel):
    """Payload to update an organizational unit."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    code: str | None = Field(default=None, max_length=50)
    unit_type: str | None = Field(default=None, max_length=50)
    parent_id: str | None = None
    description: str | None = None
    contact_email: str | None = Field(default=None, max_length=255)


class UnitResponse(BaseModel):
    """Details of an organizational unit."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    name: str
    code: str | None
    unit_type: str
    parent_id: str | None
    description: str | None
    contact_email: str | None
    created_at: datetime
    updated_at: datetime
