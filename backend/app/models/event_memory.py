"""EventMemory: structured institutional memory record for an opportunity or event.

EventMemory preserves the institutional knowledge about how an opportunity or
event was run: what worked, what didn't, attendance, outcomes, and context for
future organisers.

Records are always human-authored.  The system never auto-generates or modifies
memory content.  EventMemory is append-only: new versions must be written as
new records; the ``superseded_by_id`` field tracks the chain.

Scoped to institution workspace.  May optionally be linked to a LegacyHandover.

Migration note: introduced in Alembic revision 0006.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id


class EventMemory(TimestampMixin, Base):
    __tablename__ = "event_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Institution scoping
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The opportunity/event this memory is about.
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        index=True,
    )

    # Optional link to a handover document.
    handover_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("legacy_handovers.id", ondelete="SET NULL"),
        index=True,
    )

    # Author — the person who wrote this memory entry.
    author_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content — human-authored.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    what_worked: Mapped[str | None] = mapped_column(Text)
    what_did_not_work: Mapped[str | None] = mapped_column(Text)
    attendance_notes: Mapped[str | None] = mapped_column(Text)
    outcome_summary: Mapped[str | None] = mapped_column(Text)
    context_notes: Mapped[str | None] = mapped_column(Text)

    # Structured tags for searchability (free-text list).
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Version chain: ID of the newer record that supersedes this one.
    superseded_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("event_memories.id", ondelete="SET NULL"),
        index=True,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Extensible metadata
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    institution: Mapped[Any] = relationship(
        "Institution",
        back_populates="event_memories",
        foreign_keys=[institution_id],
    )
    opportunity: Mapped[Any] = relationship(
        "Opportunity",
        back_populates="event_memories",
        foreign_keys=[opportunity_id],
    )
    handover: Mapped[Any] = relationship(
        "LegacyHandover",
        back_populates="event_memories",
        foreign_keys=[handover_id],
    )
    author: Mapped[Any] = relationship(
        "User",
        back_populates="authored_event_memories",
        foreign_keys=[author_user_id],
    )
    superseded_by: Mapped[Any] = relationship(
        "EventMemory",
        remote_side="EventMemory.id",
        foreign_keys=[superseded_by_id],
    )
    media_assets: Mapped[list[Any]] = relationship(
        "MediaAsset",
        back_populates="event_memory",
        cascade="all, delete-orphan",
        uselist=True,
    )

    __table_args__ = (
        Index("ix_event_memories_inst_current", "institution_id", "is_current"),
        Index("ix_event_memories_opportunity", "opportunity_id", "is_current"),
    )
