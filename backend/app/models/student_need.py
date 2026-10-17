"""StudentNeed: a specific gap or blocker that a student declares they need help with.

A need is always self-reported by the student.  The platform must not infer,
fabricate, or modify need declarations.  Students decide what they need; the
matching engine only surfaces relevant help.

Each need is scoped to an institution workspace and linked to the student's
profile.  Needs have an explicit lifecycle so a student can close or pause
them once resolved.

Migration note: introduced in Alembic revision 0006.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id


class NeedStatus(enum.StrEnum):
    """Lifecycle status of a declared student need."""

    OPEN = "open"
    """Need is active and eligible for matching."""

    MATCHED = "matched"
    """At least one helper match has been proposed."""

    RESOLVED = "resolved"
    """Student has marked this need as resolved."""

    WITHDRAWN = "withdrawn"
    """Student withdrew the need before resolution."""


class NeedUrgency(enum.StrEnum):
    """Self-reported urgency level for the need."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StudentNeed(TimestampMixin, Base):
    __tablename__ = "student_needs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Ownership & institutional context
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Need content — student-authored, never system-modified.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Category aligned with HelpOffer.category for matching (free text, not FK).
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Preferred delivery mode (mirrors HelpOffer) — advisory for matcher.
    preferred_delivery_mode: Mapped[str | None] = mapped_column(String(64))

    # Urgency as declared by the student.
    urgency: Mapped[NeedUrgency] = mapped_column(
        Enum(
            NeedUrgency,
            native_enum=False,
            length=16,
            create_constraint=True,
            name="need_urgency",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=NeedUrgency.MEDIUM,
    )

    # Lifecycle state.
    status: Mapped[NeedStatus] = mapped_column(
        Enum(
            NeedStatus,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="need_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=NeedStatus.OPEN,
        index=True,
    )

    # Extensible metadata for future structured fields.
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    student_profile: Mapped[Any] = relationship(
        "StudentProfile",
        back_populates="needs",
        foreign_keys=[student_profile_id],
    )
    institution: Mapped[Any] = relationship(
        "Institution",
        back_populates="student_needs",
        foreign_keys=[institution_id],
    )
    matches: Mapped[list[Any]] = relationship(
        "HelperMatch",
        back_populates="need",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_student_needs_inst_status", "institution_id", "status"),
        Index("ix_student_needs_inst_category", "institution_id", "category"),
    )
