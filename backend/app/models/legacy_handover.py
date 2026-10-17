"""LegacyHandover: structured knowledge transfer from an outgoing role holder
to the incoming person who will continue the work.

Handovers preserve institutional knowledge across leadership transitions.
They are campus-position-scoped and always initiated by the outgoing holder.

A handover captures:
- What was done (summary of tenure accomplishments)
- What is in progress (ongoing work the successor should continue)
- Key contacts and relationships
- Pitfalls and hard-won lessons
- Recommended first steps for the incoming person

Handovers are versioned: if a new one supersedes an old one for the same
position, the old one is marked SUPERSEDED.

Migration note: introduced in Alembic revision 0006.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id


class HandoverStatus(enum.StrEnum):
    """Lifecycle of a legacy handover document."""

    DRAFT = "draft"
    """Being prepared by the outgoing holder."""

    SUBMITTED = "submitted"
    """Submitted for the incoming holder to review."""

    ACKNOWLEDGED = "acknowledged"
    """Incoming holder confirmed receipt and review."""

    SUPERSEDED = "superseded"
    """A newer handover for the same position has replaced this one."""


class LegacyHandover(TimestampMixin, Base):
    __tablename__ = "legacy_handovers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Institution scoping
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Campus position this handover is for.
    position_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("campus_position_definitions.id", ondelete="SET NULL"),
        index=True,
    )

    # Outgoing role holder (author of this handover).
    outgoing_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Incoming role holder — may be null if not yet determined.
    incoming_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    # Human-authored sections
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    accomplishments_summary: Mapped[str | None] = mapped_column(Text)
    ongoing_work: Mapped[str | None] = mapped_column(Text)
    key_contacts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    lessons_learned: Mapped[str | None] = mapped_column(Text)
    recommended_first_steps: Mapped[str | None] = mapped_column(Text)

    # Versioning: monotonically incrementing within a position.
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    # Lifecycle
    status: Mapped[HandoverStatus] = mapped_column(
        Enum(
            HandoverStatus,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="handover_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=HandoverStatus.DRAFT,
        index=True,
    )

    # When the incoming holder acknowledged receipt.
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # Relationships
    institution: Mapped[Any] = relationship(
        "Institution",
        back_populates="legacy_handovers",
        foreign_keys=[institution_id],
    )
    position: Mapped[Any] = relationship(
        "CampusPositionDefinition",
        back_populates="handovers",
        foreign_keys=[position_id],
    )
    outgoing_user: Mapped[Any] = relationship(
        "User",
        back_populates="outgoing_handovers",
        foreign_keys=[outgoing_user_id],
    )
    incoming_user: Mapped[Any] = relationship(
        "User",
        back_populates="incoming_handovers",
        foreign_keys=[incoming_user_id],
    )
    event_memories: Mapped[list[Any]] = relationship(
        "EventMemory",
        back_populates="handover",
        cascade="all, delete-orphan",
    )
    follow_up_tasks: Mapped[list[Any]] = relationship(
        "FollowUpTask",
        back_populates="handover",
        cascade="all, delete-orphan",
        foreign_keys="FollowUpTask.handover_id",
    )

    __table_args__ = (
        Index("ix_legacy_handovers_inst_status", "institution_id", "status"),
        Index("ix_legacy_handovers_position", "position_id", "version"),
    )
