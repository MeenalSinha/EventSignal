"""Cross-college promotion campaign models for EventSignal Phase 8.

Enables verified campus event organizers to promote an event across partner
institutions with explicit commercial terms, reviewer approval, and clear
'Sponsored' / 'Paid Promotion' labeling.

CRITICAL ARCHITECTURAL GUARANTEE:
Cross-college paid promotion NEVER modifies the underlying evidence evaluation
or organic recommendation score of an opportunity.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UTCDateTime, new_id


class CampaignStatus(enum.StrEnum):
    """Lifecycle stages of a cross-college promotion campaign."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class CampaignType(enum.StrEnum):
    """Placement formats available for promotional campaigns."""

    FEATURED_SPOTLIGHT = "featured_spotlight"
    CAMPUS_BULLETIN = "campus_bulletin"
    CROSS_COLLEGE_BANNER = "cross_college_banner"


class PromotionCampaign(TimestampMixin, Base):
    """Cross-college promotional campaign request and tracking record."""

    __tablename__ = "promotion_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Originating institution
    source_institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The actual opportunity/event being promoted
    opportunity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Authorized organizer who created the campaign
    creator_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # List of target institution IDs authorized to receive the campaign
    target_institution_ids: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    campaign_type: Mapped[CampaignType] = mapped_column(
        Enum(CampaignType, name="campaign_type"),
        default=CampaignType.FEATURED_SPOTLIGHT,
        nullable=False,
    )

    pricing_package: Mapped[str] = mapped_column(
        String(100), default="standard_cross_college", nullable=False
    )
    price_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    start_date: Mapped[Any] = mapped_column(UTCDateTime, nullable=False)
    end_date: Mapped[Any] = mapped_column(UTCDateTime, nullable=False)

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.DRAFT,
        nullable=False,
        index=True,
    )

    reviewer_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Conspicuous disclosure: always True for commercial campaigns
    is_paid_placement: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (Index("ix_campaign_source_status", "source_institution_id", "status"),)
