"""CampusPositionDefinition and CampusRoleAssignment: official leadership and appointed roles.

Distinguishes verified institutional appointments (e.g. "Placement Lead", "Alumni Chair",
"HOD", "Student Ambassador") from self-reported preferences. Supports time-bounded tenures
and administrative verification.

Migration note: introduced in Alembic revision 0004.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.organizational_unit import OrganizationalUnit
    from app.models.user import User


class AssignmentVerificationStatus(enum.StrEnum):
    """Authenticity verification status of an official appointment."""

    UNVERIFIED = "unverified"
    """Self-nominated or pending campus admin sign-off."""

    VERIFIED = "verified"
    """Officially confirmed by campus authority."""

    REJECTED = "rejected"
    """Rejected or revoked by campus authority."""


class CampusPositionDefinition(TimestampMixin, Base):
    """Catalogue of official positions defined by an institution."""

    __tablename__ = "campus_position_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizational_units.id", ondelete="SET NULL"), index=True
    )

    # Position title: e.g. "Placement Coordinator", "Alumni Chapter Lead", "HOD"
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # Position scope and responsibilities
    description: Mapped[str | None] = mapped_column(Text)

    # Whether this position grants official institutional leadership or sign-off authority
    is_leadership: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    institution: Mapped[Institution] = relationship(back_populates="positions")
    unit: Mapped[OrganizationalUnit | None] = relationship(back_populates="positions")
    assignments: Mapped[list[CampusRoleAssignment]] = relationship(
        back_populates="position",
        cascade="all, delete-orphan",
    )


class CampusRoleAssignment(TimestampMixin, Base):
    """Appointment of a user to an official campus position for a defined tenure."""

    __tablename__ = "campus_role_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campus_position_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizational_units.id", ondelete="SET NULL"), index=True
    )

    # Time-bounded tenure
    start_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # Active status of assignment
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Official verification tracking
    verification_status: Mapped[AssignmentVerificationStatus] = mapped_column(
        Enum(
            AssignmentVerificationStatus,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="assignment_verification_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=AssignmentVerificationStatus.UNVERIFIED,
    )
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    verified_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Relationships
    institution: Mapped[Institution] = relationship(back_populates="role_assignments")
    user: Mapped[User] = relationship(back_populates="role_assignments", foreign_keys=[user_id])
    position: Mapped[CampusPositionDefinition] = relationship(back_populates="assignments")
    unit: Mapped[OrganizationalUnit | None] = relationship(back_populates="role_assignments")
    verified_by: Mapped[User | None] = relationship(foreign_keys=[verified_by_user_id])
