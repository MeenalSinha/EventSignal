"""HelpOffer: explicit declared assistance offered by an institution member.

Examples of help include portfolio reviews, mock interviews, career guidance,
project feedback, research advice, technical mentoring, internship prep, etc.
Offers are explicitly created and published by their owner and scoped to an
institution workspace.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id


class HelpOfferStatus(enum.StrEnum):
    """Lifecycle status of a published help offer."""

    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DRAFT = "draft"


class HelpOfferAudience(enum.StrEnum):
    """Intended audience for this assistance."""

    ALL = "all"
    STUDENTS_ONLY = "students_only"
    ALUMNI_ONLY = "alumni_only"


class HelpOfferDeliveryMode(enum.StrEnum):
    """How the assistance is provided."""

    REMOTE = "remote"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"
    ASYNC = "async"


class HelpOffer(TimestampMixin, Base):
    __tablename__ = "help_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Ownership & workspace scoping
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membership_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("institution_memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Offer details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applicable_skills: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audience and delivery preferences
    intended_audience: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=HelpOfferAudience.ALL.value,
    )
    delivery_mode: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=HelpOfferDeliveryMode.REMOTE.value,
    )
    availability_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle & explicit consent
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=HelpOfferStatus.ACTIVE.value,
        index=True,
    )
    willing_to_help: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Extensible metadata
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped[Any] = relationship("User", back_populates="help_offers", foreign_keys=[user_id])
    institution: Mapped[Any] = relationship(
        "Institution", back_populates="help_offers", foreign_keys=[institution_id]
    )

    __table_args__ = (
        Index("ix_help_offers_inst_status", "institution_id", "status"),
        Index("ix_help_offers_inst_category", "institution_id", "category"),
    )
