"""ConnectionRequest: purpose-specific professional connection between a student and an alumni.

Connection requests may only be sent when the recipient alumni profile has
``willing_to_connect = True``. The request must include a stated purpose so
the recipient can make an informed decision.

A request is not a social network follow. It is a professional contact
initiated with explicit purpose and subject to the alumni's consent.

Migration note: introduced in Alembic revision 0001.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id


class ConnectionPurpose(enum.StrEnum):
    """Why the student wants to connect. Must be stated explicitly."""

    CAREER_GUIDANCE = "career_guidance"
    """Seeking advice on career paths or professional decisions."""

    OPPORTUNITY_SPECIFIC = "opportunity_specific"
    """Discussing a specific opportunity that the alumni is relevant to."""

    SKILL_MENTORING = "skill_mentoring"
    """Seeking help developing a specific skill or domain area."""

    INDUSTRY_INSIGHT = "industry_insight"
    """Learning about an industry or company from someone with experience."""

    REFERRAL = "referral"
    """Asking for an introduction or referral to someone in the alum's network."""

    OTHER = "other"
    """Purpose not covered by the above. Message must explain."""


class RequestStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class ConnectionRequest(TimestampMixin, Base):
    __tablename__ = "connection_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    requester_profile_id: Mapped[str] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_profile_id: Mapped[str] = mapped_column(
        ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    purpose: Mapped[ConnectionPurpose] = mapped_column(
        Enum(
            ConnectionPurpose,
            native_enum=False,
            length=32,
            create_constraint=True,
            name="connection_purpose",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
    )

    # Optional message. Must not be fabricated or generated on behalf of the student.
    message: Mapped[str | None] = mapped_column(Text)

    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            native_enum=False,
            length=16,
            create_constraint=True,
            name="request_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=RequestStatus.PENDING,
    )

    # Set when the recipient acts on the request.
    responded_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
