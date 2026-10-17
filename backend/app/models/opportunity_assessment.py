"""OpportunityAssessment: persisted evaluation of an ingested opportunity.

Phase 4 introduces a deterministic assessment engine that evaluates each
ingested opportunity across five dimensions and persists the results here.

One assessment per opportunity is stored; re-running assessment replaces it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id

if TYPE_CHECKING:
    from app.models.opportunity import Opportunity


class OpportunityAssessment(TimestampMixin, Base):
    __tablename__ = "opportunity_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One assessment per opportunity
    )

    # --- Scores (0.0 - 1.0) -------------------------------------------
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, nullable=False)

    # --- Explanations -----------------------------------------------------
    completeness_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_quality_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    consistency_explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Policy version ---------------------------------------------------
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")

    # --- Field lists (stored as JSON arrays of field name strings) --------
    missing_critical_fields: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    missing_optional_fields: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    ambiguous_fields: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    conflicting_fields: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    conflict_details: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

    # --- Limitations paragraph --------------------------------------------
    limitations: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Evidence snapshot at assessment time ----------------------------
    total_fields_assessed: Mapped[int] = mapped_column(Integer, nullable=False)
    fields_found_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fields_not_found_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fields_failed_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Relationships ----------------------------------------------------
    opportunity: Mapped[Opportunity] = relationship(back_populates="assessment")
