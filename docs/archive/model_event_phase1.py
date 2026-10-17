"""Event model, compatible with the Phase 0 event information schema.

Every published-information column is nullable: a field being important to check
does not mean every event has a value for it. Distinguishing missing, inapplicable,
failed and conflicting values is the job of the evidence layer added in a later
phase, which will reference ``events.id`` and a field name.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id

if TYPE_CHECKING:
    from app.models.source_reference import SourceReference


class EventMode(enum.StrEnum):
    """Participation mode, only when the source states it."""

    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    event_name: Mapped[str | None] = mapped_column(String(300))
    organizer: Mapped[str | None] = mapped_column(String(300))

    start_date: Mapped[datetime | None] = mapped_column(UTCDateTime)
    end_date: Mapped[datetime | None] = mapped_column(UTCDateTime)
    registration_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime)
    submission_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime)

    venue: Mapped[str | None] = mapped_column(String(500))
    mode: Mapped[EventMode | None] = mapped_column(
        Enum(
            EventMode,
            native_enum=False,
            length=16,
            create_constraint=True,
            name="event_mode",
            values_callable=lambda members: [member.value for member in members],
        )
    )

    # Stored as published (free text); structured interpretation belongs to later phases.
    eligibility: Mapped[str | None] = mapped_column(Text)
    participation_fee: Mapped[str | None] = mapped_column(Text)
    agenda: Mapped[str | None] = mapped_column(Text)
    prizes_and_benefits: Mapped[str | None] = mapped_column(Text)
    registration_url: Mapped[str | None] = mapped_column(String(2048))

    # ``source_urls`` from the Phase 0 schema is modelled as a relationship, not a string.
    sources: Mapped[list[SourceReference]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="SourceReference.created_at",
    )
