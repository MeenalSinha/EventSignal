"""InstitutionMembership: authorized members and role-based access control.

Each member belongs to an institution with a specific institutional role
(Platform Admin, Institution Admin, Faculty, Student, Alumni, Member) and status.

Migration note: introduced in Alembic revision 0004.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id, utcnow

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class InstitutionRole(enum.StrEnum):
    """Institutional role assigning permission scope."""

    PLATFORM_ADMIN = "platform_admin"
    """System-level oversight across institutions."""

    INSTITUTION_ADMIN = "institution_admin"
    """College administrator: can manage units, leaders, members, settings."""

    FACULTY = "faculty"
    """Faculty or institutional staff member."""

    STUDENT = "student"
    """Enrolled student at the institution."""

    ALUMNI = "alumni"
    """Graduate or alumnus/alumna of the institution."""

    MEMBER = "member"
    """General affiliated community member."""


class MembershipStatus(enum.StrEnum):
    """Membership lifecycle status."""

    PENDING = "pending"
    """Awaiting verification or approval by campus admin."""

    ACTIVE = "active"
    """Active member with workspace privileges."""

    SUSPENDED = "suspended"
    """Temporarily inactive."""

    REVOKED = "revoked"
    """Affiliation terminated."""


class InstitutionMembership(TimestampMixin, Base):
    __tablename__ = "institution_memberships"
    __table_args__ = (
        UniqueConstraint("institution_id", "user_id", name="uq_institution_user_membership"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role: Mapped[InstitutionRole] = mapped_column(
        Enum(
            InstitutionRole,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="institution_role",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=InstitutionRole.STUDENT,
    )

    status: Mapped[MembershipStatus] = mapped_column(
        Enum(
            MembershipStatus,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="membership_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=MembershipStatus.ACTIVE,
    )

    joined_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    # Verification of institutional affiliation
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    verified_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Relationships
    institution: Mapped[Institution] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships", foreign_keys=[user_id])
    verified_by: Mapped[User | None] = relationship(foreign_keys=[verified_by_user_id])
