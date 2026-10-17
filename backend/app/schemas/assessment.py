"""Schemas for Phase 4 opportunity assessment endpoints.

The assessment evaluates ingested opportunities across five dimensions
and returns structured, explainable results that students can use to
make informed decisions about opportunities.

Assessment dimensions:
  1. Completeness     — how many expected fields have values.
  2. Evidence quality — reliability of extraction methods used.
  3. Consistency      — absence of source conflicts (stub for single-source).
  4. Missing fields   — which critical and optional fields are absent.
  5. Ambiguous/conflicting — which fields carry uncertainty or conflict.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OpportunityAssessmentRead(BaseModel):
    """Full assessment result for a single opportunity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    policy_version: str = "1.0.0"

    # Composite score
    overall_score: float = Field(ge=0.0, le=1.0)

    # Dimension scores
    completeness_score: float = Field(ge=0.0, le=1.0)
    evidence_quality_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)

    # Human-readable explanations for each dimension
    completeness_explanation: str
    evidence_quality_explanation: str
    consistency_explanation: str

    # Field categorisation
    missing_critical_fields: list[str]
    missing_optional_fields: list[str]
    ambiguous_fields: list[str]
    conflicting_fields: list[str]
    conflict_details: list[dict[str, Any]] = Field(default_factory=list)

    # Limitations paragraph — describes what the system cannot determine
    limitations: str

    # Evidence snapshot at assessment time
    total_fields_assessed: int = Field(ge=0)
    fields_found_count: int = Field(ge=0)
    fields_not_found_count: int = Field(ge=0)
    fields_failed_count: int = Field(ge=0)


class AssessmentScoreSummary(BaseModel):
    """Compact score card — used in opportunity list views."""

    overall_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
    evidence_quality_score: float = Field(ge=0.0, le=1.0)
    fields_found_count: int
    total_fields_assessed: int
    missing_critical_count: int
