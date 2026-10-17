"""FollowUpTask: an actionable task generated from a LegacyHandover or HelperMatch.

Tasks make recommendations concrete and trackable.  They are always explicitly
assigned to a person and tied to either a handover or a match.  The platform
never auto-completes tasks; completion is always asserted by the assignee.

Tasks are simple and opinionated by design.  They capture what to do, by when,
and current completion state.  Priority is self-reported by the creator.

Migration note: introduced in Alembic revision 0006.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id


class TaskPriority(enum.StrEnum):
    """Self-reported urgency of the task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskSource(enum.StrEnum):
    """Where this task was generated from."""

    HANDOVER = "handover"
    """Generated from a LegacyHandover document."""

    MATCH = "match"
    """Generated after a HelperMatch was accepted."""

    MANUAL = "manual"
    """Explicitly created by a user without a triggering event."""


class FollowUpTask(TimestampMixin, Base):
    __tablename__ = "follow_up_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Institution scoping
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source of this task — exactly one of handover_id / match_id will be set
    # unless source == MANUAL.
    source: Mapped[TaskSource] = mapped_column(
        Enum(
            TaskSource,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="task_source",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=TaskSource.MANUAL,
        index=True,
    )
    handover_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("legacy_handovers.id", ondelete="SET NULL"),
        index=True,
    )
    match_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("helper_matches.id", ondelete="SET NULL"),
        index=True,
    )

    # Task content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Assigned to this user.
    assignee_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Created by this user.
    creator_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # When this task should be done by (optional, self-reported).
    due_date: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # Priority — self-reported by creator.
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(
            TaskPriority,
            native_enum=False,
            length=16,
            create_constraint=True,
            name="task_priority",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True,
    )

    # Completion state — asserted only by the assignee.
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # Extensible metadata
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    institution: Mapped[Any] = relationship(
        "Institution",
        back_populates="follow_up_tasks",
        foreign_keys=[institution_id],
    )
    handover: Mapped[Any] = relationship(
        "LegacyHandover",
        back_populates="follow_up_tasks",
        foreign_keys=[handover_id],
    )
    match: Mapped[Any] = relationship(
        "HelperMatch",
        back_populates="follow_up_tasks",
        foreign_keys=[match_id],
    )
    assignee: Mapped[Any] = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_user_id],
    )
    creator: Mapped[Any] = relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[creator_user_id],
    )

    __table_args__ = (
        Index("ix_follow_up_tasks_inst_completed", "institution_id", "is_completed"),
        Index("ix_follow_up_tasks_assignee_completed", "assignee_user_id", "is_completed"),
    )
