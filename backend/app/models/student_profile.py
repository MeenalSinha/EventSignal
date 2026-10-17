"""StudentProfile: self-reported career goals and preferences.

Information here is declared by the student themselves. It is not verified
by the platform and must not be presented as independently confirmed.

Visibility: profile data is used for matching only. Sharing outside the
matching context requires explicit consent in a later phase.

Migration note: introduced in Alembic revision 0001.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_id


class ProfileVisibility(enum.StrEnum):
    """Controls who can see this profile."""

    PRIVATE = "private"
    """Only the owner and system processes can see this profile."""

    ALUMNI_ONLY = "alumni_only"
    """Visible to alumni and mentors who are potential connection recipients."""

    PUBLIC = "public"
    """Visible to all authenticated platform users."""


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Display name — self-reported, not verified.
    display_name: Mapped[str | None] = mapped_column(String(200))

    # Skills, interests and goals are stored as free text in this phase.
    # Structured taxonomies belong to a later phase.
    skills: Mapped[str | None] = mapped_column(Text)
    interests: Mapped[str | None] = mapped_column(Text)
    career_goals: Mapped[str | None] = mapped_column(Text)

    # Comma-separated opportunity types the student is interested in (free text now).
    preferred_opportunity_types: Mapped[str | None] = mapped_column(Text)

    # Location or participation preference — self-described.
    location_preference: Mapped[str | None] = mapped_column(Text)

    visibility: Mapped[ProfileVisibility] = mapped_column(
        Enum(
            ProfileVisibility,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="profile_visibility",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=ProfileVisibility.PRIVATE,
    )

    # Extensible metadata bag for future structured preference fields.
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
