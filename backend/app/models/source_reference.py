"""Source references: where information about an event may come from.

A source row records provenance only. Extracted values, excerpts and evidence
statuses will live in a separate evidence table in a later phase and reference
``source_references.id``.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id

if TYPE_CHECKING:
    from app.models.event import Event


class SourceType(enum.StrEnum):
    EVENT_LISTING = "event_listing"
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
        # A URL is recorded at most once per event. NULL urls (manual text) are allowed repeatedly.
        UniqueConstraint("event_id", "url"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
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

    event: Mapped[Event] = relationship(back_populates="sources")
