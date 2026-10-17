"""Sponsorship and partner domain models for EventSignal Phase 8.

Facilitates structured sponsorship inquiries and partnership relationships
between campus event organizers and verified or prospective partners.
No automated payment gateways or fabricated sponsor interest; all terms
are explicitly tracked, verified, and scoped to the host institution.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id


class SponsorshipStatus(enum.StrEnum):
    """Lifecycle stages of a sponsorship request."""

    DRAFT = "draft"
    """Organizer is preparing the sponsorship prospectus."""

    SUBMITTED = "submitted"
    """Prospectus is formally submitted for review or outbound inquiry."""

    UNDER_REVIEW = "under_review"
    """Sponsorship coordinator or partner is reviewing the request."""

    ACCEPTED = "accepted"
    """Sponsorship agreed in principle upon defined commercial terms."""

    DECLINED = "declined"
    """Sponsorship declined by partner or institution reviewer."""

    CLOSED = "closed"
    """Event concluded and sponsorship arrangement finalized."""

    WITHDRAWN = "withdrawn"
    """Organizer cancelled the inquiry before finalization."""


class SupportType(enum.StrEnum):
    """Form of support requested from the partner."""

    FINANCIAL = "financial"
    IN_KIND = "in_kind"
    MENTORSHIP = "mentorship"
    VENUE = "venue"
    SWAG = "swag"
    OTHER = "other"


class PartnerVerificationStatus(enum.StrEnum):
    """Honest representation of partner organization status."""

    UNVERIFIED = "unverified"
    """Company name entered; representative not yet verified."""

    EXPRESSED_INTEREST = "expressed_interest"
    """Partner or organizer entered an exploratory relationship."""

    VERIFIED_REPRESENTATIVE = "verified_representative"
    """Representative's corporate identity and authority validated."""

    CONFIRMED_SPONSOR = "confirmed_sponsor"
    """Formal sponsorship history on record with this institution."""


class PartnerOrganization(TimestampMixin, Base):
    """An external organization, brand, or sponsor entity."""

    __tablename__ = "partner_organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[PartnerVerificationStatus] = mapped_column(
        Enum(PartnerVerificationStatus, name="partner_verification_status"),
        default=PartnerVerificationStatus.UNVERIFIED,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_partner_org_inst_name", "institution_id", "name"),)


class SponsorshipRequest(TimestampMixin, Base):
    """Structured sponsorship inquiry or prospectus linked to an event/opportunity."""

    __tablename__ = "sponsorship_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    opportunity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organizer_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    partner_organization_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("partner_organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    objective: Mapped[str] = mapped_column(String(255), nullable=False)
    support_type: Mapped[SupportType] = mapped_column(
        Enum(SupportType, name="sponsorship_support_type"),
        default=SupportType.FINANCIAL,
        nullable=False,
    )
    proposed_benefits: Mapped[str] = mapped_column(Text, nullable=False)
    intended_audience: Mapped[str | None] = mapped_column(String(255), nullable=True)

    budget_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    budget_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    deadline: Mapped[Any | None] = mapped_column(UTCDateTime, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[SponsorshipStatus] = mapped_column(
        Enum(SponsorshipStatus, name="sponsorship_status"),
        default=SponsorshipStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Disclosed commercial terms without automated payment processing
    commercial_terms: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_sponsorship_inst_status", "institution_id", "status"),)
