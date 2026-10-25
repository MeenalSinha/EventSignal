"""Opportunity and source-reference schemas.

``OpportunityCreate`` and ``SourceReferenceCreate`` define the validated input contract
that Phase 2 submission endpoints will reuse. They are not exposed by any route in
Phase 2. ``OpportunityRead`` and ``SourceReferenceRead`` are the output contracts.

Phase 1 note: these schemas replace the former EventCreate/EventRead contracts.
The HTTP endpoint is renamed from /events to /opportunities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.models.field_evidence import EvidenceStatus, ExtractionMethod
from app.models.opportunity import OpportunityType, ParticipationMode
from app.models.source_reference import SourceType
from app.schemas.media import MediaAssetRead

MAX_URL_LENGTH = 2048


def _validate_http_url(value: str) -> str:
    """Accept only http(s) URLs without embedded credentials."""
    value = value.strip()
    if len(value) > MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds {MAX_URL_LENGTH} characters")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must use http or https")
    if not parsed.hostname:
        raise ValueError("URL must include a host")
    if parsed.username or parsed.password:
        raise ValueError("URL must not contain embedded credentials")
    return value


HttpUrlStr = Annotated[str, AfterValidator(_validate_http_url)]


class SourceReferenceCreate(BaseModel):
    source_type: SourceType
    url: HttpUrlStr | None = None
    title: Annotated[str, Field(max_length=500)] | None = None
    retrieved_at: datetime | None = None
    content_hash: Annotated[str, Field(max_length=64)] | None = None
    source_metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _url_required_unless_manual(self) -> SourceReferenceCreate:
        if self.url is None and self.source_type is not SourceType.MANUAL_TEXT:
            raise ValueError("url is required for every source type except manual_text")
        return self

    @model_validator(mode="after")
    def _retrieved_at_is_aware(self) -> SourceReferenceCreate:
        if self.retrieved_at is not None and self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must include a timezone")
        return self


class OpportunityCreate(BaseModel):
    """Published opportunity information. Every field is optional because sources may omit it."""

    title: Annotated[str, Field(min_length=1, max_length=300)] | None = None
    opportunity_type: OpportunityType | None = None
    organizer: Annotated[str, Field(min_length=1, max_length=300)] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_deadline: datetime | None = None
    submission_deadline: datetime | None = None
    location: Annotated[str, Field(max_length=500)] | None = None
    mode: ParticipationMode | None = None
    eligibility: str | None = None
    skills_required: str | None = None
    compensation: str | None = None
    application_url: HttpUrlStr | None = None
    sources: list[SourceReferenceCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_dates(self) -> OpportunityCreate:
        for name in ("start_date", "end_date", "registration_deadline", "submission_deadline"):
            value = getattr(self, name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must include a timezone")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be earlier than start_date")
        return self


class SourceReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    source_type: SourceType
    url: str | None
    title: str | None
    retrieved_at: datetime | None
    content_hash: str | None
    source_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class FieldEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    source_id: str | None
    field_name: str
    extracted_value: str | None
    supporting_excerpt: str | None
    extraction_method: ExtractionMethod
    evidence_status: EvidenceStatus
    created_at: datetime
    updated_at: datetime


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    opportunity_type: OpportunityType | None
    organizer: str | None
    start_date: datetime | None
    end_date: datetime | None
    registration_deadline: datetime | None
    submission_deadline: datetime | None
    location: str | None
    mode: ParticipationMode | None
    eligibility: str | None
    skills_required: str | None
    compensation: str | None
    application_url: str | None
    institution_id: str | None = None
    poster_url: str | None = None
    sources: list[SourceReferenceRead]
    evidence: list[FieldEvidenceRead] = Field(default_factory=list)
    media_assets: list[MediaAssetRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class OpportunityList(BaseModel):
    items: list[OpportunityRead]
    total: int = Field(ge=0, description="Total opportunities stored, regardless of pagination.")
    limit: int
    offset: int
