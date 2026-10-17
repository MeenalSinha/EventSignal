"""Source references: provenance records for opportunity information.

Adapted from Phase 1: ``event_id`` foreign key becomes ``opportunity_id``.
The column semantics and constraints are unchanged.

Migration note: this model is updated in Alembic revision 0001.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id

if TYPE_CHECKING:
    from app.models.field_evidence import FieldEvidence
    from app.models.opportunity import Opportunity


class SourceType(enum.StrEnum):
    OPPORTUNITY_LISTING = "opportunity_listing"
    ORGANIZER_WEBSITE = "organizer_website"
    REGISTRATION_PAGE = "registration_page"
    ANNOUNCEMENT = "announcement"
    DOCUMENT = "document"
    SOCIAL_MEDIA = "social_media"
    MANUAL_TEXT = "manual_text"
    OTHER = "other"


class SourceReference(TimestampMixin, Base):
    __tablename__ = "source_references"
    __table_args__ = (
        # A URL is recorded at most once per opportunity.
        # NULL urls (manual text) are allowed repeatedly.
        UniqueConstraint("opportunity_id", "url"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    source_type: Mapped[SourceType] = mapped_column(
        Enum(
            SourceType,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="source_type",
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
    )
    # Null for sources without a URL, such as manually supplied text.
    url: Mapped[str | None] = mapped_column(String(2048))
    title: Mapped[str | None] = mapped_column(String(500))
    # Set only when content was actually retrieved.
    retrieved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    # Free-form retrieval/extraction metadata (HTTP status, content type, ...) for later phases.
    source_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    opportunity: Mapped[Opportunity] = relationship(back_populates="sources")
    evidence: Mapped[list[FieldEvidence]] = relationship(back_populates="source")
