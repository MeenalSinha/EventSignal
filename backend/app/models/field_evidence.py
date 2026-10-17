"""FieldEvidence: source-linked extracted values for individual opportunity fields.

This table forms the Phase 2 evidence layer. Each row associates one extracted
or supported value for a named opportunity field with the source it came from and
the method by which it was extracted.

Evidence statuses encode what the system actually knows — not a judgment about
the opportunity's legitimacy. See EvidenceStatus for the allowed states.

Migration note: introduced in Alembic revision 0001.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id

if TYPE_CHECKING:
    from app.models.opportunity import Opportunity
    from app.models.source_reference import SourceReference


class EvidenceStatus(enum.StrEnum):
    """What the system can establish about this field, from this source.

    These statuses describe the system's evidence state. They do not establish
    whether an opportunity is legitimate.
    """

    FOUND = "found"
    """Value was found in the source."""

    MULTI_SOURCE = "multi_source"
    """Value is supported by multiple sources that agree."""

    NEEDS_VERIFICATION = "needs_verification"
    """Value found but could not be independently confirmed."""

    NOT_FOUND = "not_found"
    """Field was specifically looked for and not found in the source."""

    SOURCES_DISAGREE = "sources_disagree"
    """Multiple sources were found but they contradict each other."""

    EXTRACTION_FAILED = "extraction_failed"
    """An attempt was made to extract the value but it failed technically.
    This is distinct from NOT_FOUND: the system tried and encountered an error."""

    NOT_ASSESSED = "not_assessed"
    """Field has not been examined for this source."""


class ExtractionMethod(enum.StrEnum):
    """How the value was obtained."""

    MANUAL = "manual"
    """Entered by a human operator."""

    RULE_BASED = "rule_based"
    """Extracted by a deterministic rule or pattern match."""

    LLM = "llm"
    """Extracted by a large language model; requires human review."""

    STRUCTURED = "structured"
    """Parsed from a structured data format (JSON-LD, schema.org, etc.)."""


class FieldEvidence(TimestampMixin, Base):
    __tablename__ = "field_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_references.id", ondelete="SET NULL"), index=True
    )

    # The model attribute name being evidenced (e.g. "title", "start_date").
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # The extracted or supported value as a string representation. NULL means absence was found.
    extracted_value: Mapped[str | None] = mapped_column(Text)
    # The raw excerpt from the source that supports this value.
    supporting_excerpt: Mapped[str | None] = mapped_column(Text)

    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        Enum(
            ExtractionMethod,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="extraction_method",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
    )
    evidence_status: Mapped[EvidenceStatus] = mapped_column(
        Enum(
            EvidenceStatus,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="evidence_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=EvidenceStatus.NOT_ASSESSED,
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="evidence")
    source: Mapped[SourceReference | None] = relationship(back_populates="evidence")
