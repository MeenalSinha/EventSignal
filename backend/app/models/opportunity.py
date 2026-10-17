"""Opportunity model: the primary entity students discover and evaluate.

Evolved from the Phase 1 ``Event`` model; the table name and type enum are
changed, but the column semantics are preserved. Every published-information
column is nullable — a field being important to check does not mean every
opportunity publishes a value for it.

Migration note: this model corresponds to Alembic revision 0001.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id

if TYPE_CHECKING:
    from app.models.event_memory import EventMemory
    from app.models.field_evidence import FieldEvidence
    from app.models.institution import Institution
    from app.models.opportunity_assessment import OpportunityAssessment
    from app.models.source_reference import SourceReference


class OpportunityType(enum.StrEnum):
    """Broad category of the opportunity."""

    HACKATHON = "hackathon"
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    COMPETITION = "competition"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    RESEARCH = "research"
    MENTORSHIP = "mentorship"
    OTHER = "other"


class ParticipationMode(enum.StrEnum):
    """Participation mode, only when the source states it."""

    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    title: Mapped[str | None] = mapped_column(String(300))
    opportunity_type: Mapped[OpportunityType | None] = mapped_column(
        Enum(
            OpportunityType,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="opportunity_type",
            values_callable=lambda members: [m.value for m in members],
        )
    )
    organizer: Mapped[str | None] = mapped_column(String(300))

    start_date: Mapped[datetime | None] = mapped_column(UTCDateTime)
    end_date: Mapped[datetime | None] = mapped_column(UTCDateTime)
    registration_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime)
    submission_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime)

    location: Mapped[str | None] = mapped_column(String(500))
    mode: Mapped[ParticipationMode | None] = mapped_column(
        Enum(
            ParticipationMode,
            native_enum=False,
            length=16,
            create_constraint=True,
            name="participation_mode",
            values_callable=lambda members: [m.value for m in members],
        )
    )

    # Stored as published free text; structured interpretation via FieldEvidence.
    eligibility: Mapped[str | None] = mapped_column(Text)
    # Skills and interests as free text; structured matching belongs to later phases.
    skills_required: Mapped[str | None] = mapped_column(Text)
    # Compensation, prize, or cost information, as published.
    compensation: Mapped[str | None] = mapped_column(Text)
    application_url: Mapped[str | None] = mapped_column(String(2048))

    # ``sources`` replaces the Phase 1 ``source_urls`` string column.
    sources: Mapped[list[SourceReference]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
        order_by="SourceReference.created_at",
    )

    # Evidence records (added Phase 2; populated by future extraction pipeline).
    evidence: Mapped[list[FieldEvidence]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )

    # Assessment result (added Phase 4; one-to-one, created on demand).
    assessment: Mapped[OpportunityAssessment | None] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # Scoped institutional workspace (added Phase 5; None indicates platform-wide)
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="SET NULL"), index=True
    )
    institution: Mapped[Institution | None] = relationship(
        back_populates="opportunities",
    )
    event_memories: Mapped[list[EventMemory]] = relationship(
        back_populates="opportunity",
        foreign_keys="[EventMemory.opportunity_id]",
    )
