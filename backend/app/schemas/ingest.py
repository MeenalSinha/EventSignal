"""Schemas for opportunity intake / ingestion workflow.

Follows the existing Pydantic validation conventions and integrates with
OpportunityRead, SourceReferenceRead, and FieldEvidenceRead.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.opportunity import (
    FieldEvidenceRead,
    HttpUrlStr,
    OpportunityRead,
    SourceReferenceRead,
)


class OpportunityIngestRequest(BaseModel):
    """Request payload to submit a publicly accessible opportunity URL."""

    url: HttpUrlStr = Field(description="Public HTTP or HTTPS opportunity URL.")
    force_refresh: bool = Field(
        default=False,
        description="If True, re-fetch and re-extract even if URL already exists.",
    )


class OpportunityIngestResponse(BaseModel):
    """Result of ingesting an opportunity URL."""

    opportunity: OpportunityRead
    source_reference: SourceReferenceRead
    is_duplicate: bool = Field(
        default=False,
        description="True if this URL had already been ingested and was returned without refresh.",
    )
    fields_extracted_count: int = Field(
        ge=0,
        description="Number of fields genuinely found and extracted with FOUND status.",
    )
    evidence: list[FieldEvidenceRead] = Field(
        default_factory=list,
        description="Field-level evidence records supporting the opportunity.",
    )
    message: str = Field(description="Human-readable result summary.")
