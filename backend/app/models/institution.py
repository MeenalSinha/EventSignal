"""Institution model: participating colleges and their isolated workspaces.

Each participating college has its own persistent workspace, managed organizational
units, authorized memberships, and official campus positions.

Migration note: introduced in Alembic revision 0004.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.campus_position import CampusPositionDefinition, CampusRoleAssignment
    from app.models.membership import InstitutionMembership
    from app.models.opportunity import Opportunity
    from app.models.organizational_unit import OrganizationalUnit


class InstitutionStatus(enum.StrEnum):
    """Lifecycle status of the institution workspace."""

    PENDING = "pending"
    """Onboarded but awaiting initial platform activation."""

    ACTIVE = "active"
    """Fully operational workspace."""

    SUSPENDED = "suspended"
    """Temporarily locked or archived."""


class InstitutionVerificationStatus(enum.StrEnum):
    """Institutional identity authenticity verification."""

    UNVERIFIED = "unverified"
    """Self-registered or pending verification."""

    VERIFIED = "verified"
    """Confirmed official higher education institution."""

    REJECTED = "rejected"
    """Failed authenticity verification."""


class Institution(TimestampMixin, Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Full institutional name: e.g. "Indraprastha Institute of Information Technology Delhi"
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # URL-friendly workspace slug: e.g. "iiitd"
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Primary academic domain: e.g. "iiitd.ac.in"
    domain: Mapped[str | None] = mapped_column(String(255), index=True)

    # Institutional profile & overview
    description: Mapped[str | None] = mapped_column(Text)

    # Physical campus location: City, State, Country
    location: Mapped[str | None] = mapped_column(String(255))

    # Official contact email and website URL
    contact_email: Mapped[str | None] = mapped_column(String(255))
    website_url: Mapped[str | None] = mapped_column(String(1024))

    # Workspace status & identity verification
    status: Mapped[InstitutionStatus] = mapped_column(
        Enum(
            InstitutionStatus,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="institution_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=InstitutionStatus.ACTIVE,
    )

    verification_status: Mapped[InstitutionVerificationStatus] = mapped_column(
        Enum(
            InstitutionVerificationStatus,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="institution_verification_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=InstitutionVerificationStatus.UNVERIFIED,
    )

    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    # Extensible metadata (branding, colors, settings, accreditations)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    memberships: Mapped[list[InstitutionMembership]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    units: Mapped[list[OrganizationalUnit]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list[CampusPositionDefinition]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    role_assignments: Mapped[list[CampusRoleAssignment]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    opportunities: Mapped[list[Opportunity]] = relationship(
        back_populates="institution",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="institution",
    )
