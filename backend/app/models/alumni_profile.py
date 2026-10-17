"""AlumniProfile: self-reported expertise and declared mentoring availability.

Information here is declared by the alumni themselves. It is not verified
by the platform and must not be presented as independently confirmed.

Willingness to receive connection requests is explicit and required. No
connection request may be sent to a profile whose ``willing_to_connect``
flag is False.

Ownership: linked to authenticated User and Institution workspace.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id


class ProfileVisibility(enum.StrEnum):
    """Controls who can see this profile."""

    PRIVATE = "private"
    STUDENTS_ONLY = "students_only"
    PUBLIC = "public"


class AlumniProfile(TimestampMixin, Base):
    __tablename__ = "alumni_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Ownership & institutional context
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    institution_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    membership_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("institution_memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Display name — self-reported, not verified.
    display_name: Mapped[str | None] = mapped_column(String(200))

    # Professional domain: e.g. "Software Engineering", "Biotech". Free text.
    professional_domain: Mapped[str | None] = mapped_column(String(200))

    # Skills and industry — self-described.
    skills: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)

    # Years of experience — self-reported integer.
    years_experience: Mapped[int | None] = mapped_column()

    # What the alum is willing to help with — free text.
    mentoring_interests: Mapped[str | None] = mapped_column(Text)

    # Explicit consent to receive connection requests. False = no requests may be sent.
    willing_to_connect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Maximum connections per month the alum is comfortable handling — advisory.
    monthly_connection_limit: Mapped[int | None] = mapped_column()

    visibility: Mapped[ProfileVisibility] = mapped_column(
        Enum(
            ProfileVisibility,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="alumni_profile_visibility",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=ProfileVisibility.PRIVATE,
    )

    # Extensible metadata bag for future structured fields.
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    user: Mapped[Any] = relationship(
        "User", back_populates="alumni_profiles", foreign_keys=[user_id]
    )
    institution: Mapped[Any] = relationship(
        "Institution", back_populates="alumni_profiles", foreign_keys=[institution_id]
    )

    __table_args__ = (
        UniqueConstraint("user_id", "institution_id", name="uq_alumni_profile_user_institution"),
    )
