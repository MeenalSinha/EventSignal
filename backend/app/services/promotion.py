"""Cross-college promotion service for EventSignal Phase 8.

Handles campaign pricing packages, lifecycle state transitions, reviewer
approvals, and cross-institution sponsored feed queries.

CRITICAL ARCHITECTURAL GUARANTEE:
Cross-college paid promotion NEVER modifies the underlying evidence evaluation
or organic recommendation score of an opportunity.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.institution import Institution
from app.models.opportunity import Opportunity
from app.models.promotion_campaign import CampaignStatus, CampaignType, PromotionCampaign
from app.schemas.phase8 import FeedPromotionItem, PricingPackageRead

AVAILABLE_PRICING_PACKAGES: dict[str, dict[str, Any]] = {
    "standard_cross_college": {
        "name": "Standard Cross-College Placement",
        "description": "Featured placement on partner campus opportunity bulletins.",
        "price_amount": 49.00,
        "currency": "USD",
        "duration_days": 7,
        "placement_type": "campus_bulletin",
    },
    "spotlight_multicampus": {
        "name": "Multicampus Spotlight Banner",
        "description": "Top-tier banner placement across all selected partner institutions.",
        "price_amount": 99.00,
        "currency": "USD",
        "duration_days": 14,
        "placement_type": "featured_spotlight",
    },
    "pilot_free": {
        "name": "Pilot Cohort Sponsored Placement",
        "description": "Complimentary promotion package for pilot partner institutions.",
        "price_amount": 0.00,
        "currency": "USD",
        "duration_days": 30,
        "placement_type": "cross_college_banner",
    },
}

VALID_CAMPAIGN_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
    CampaignStatus.DRAFT: {CampaignStatus.SUBMITTED, CampaignStatus.CANCELLED},
    CampaignStatus.SUBMITTED: {
        CampaignStatus.UNDER_REVIEW,
        CampaignStatus.APPROVED,
        CampaignStatus.REJECTED,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.UNDER_REVIEW: {
        CampaignStatus.APPROVED,
        CampaignStatus.REJECTED,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.APPROVED: {
        CampaignStatus.SCHEDULED,
        CampaignStatus.ACTIVE,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.SCHEDULED: {CampaignStatus.ACTIVE, CampaignStatus.CANCELLED},
    CampaignStatus.ACTIVE: {CampaignStatus.COMPLETED, CampaignStatus.CANCELLED},
    CampaignStatus.COMPLETED: set(),
    CampaignStatus.REJECTED: set(),
    CampaignStatus.CANCELLED: set(),
}


class PromotionService:
    @staticmethod
    def get_pricing_packages() -> list[PricingPackageRead]:
        return [
            PricingPackageRead(
                package_id=pkg_id,
                name=info["name"],
                description=info["description"],
                price_amount=info["price_amount"],
                currency=info["currency"],
                duration_days=info["duration_days"],
                placement_type=info["placement_type"],
            )
            for pkg_id, info in AVAILABLE_PRICING_PACKAGES.items()
        ]

    @staticmethod
    def create_campaign(
        db: Session,
        source_institution_id: str,
        creator_user_id: str,
        opportunity_id: str,
        target_institution_ids: list[str],
        campaign_type: CampaignType = CampaignType.FEATURED_SPOTLIGHT,
        pricing_package: str = "standard_cross_college",
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> PromotionCampaign:
        # Validate opportunity exists
        opp = db.scalar(select(Opportunity).where(Opportunity.id == opportunity_id))
        if not opp:
            raise LookupError("Referenced opportunity does not exist")

        # Validate target institutions exist
        if not target_institution_ids:
            raise ValueError("At least one target institution must be specified")

        for tid in target_institution_ids:
            target_inst = db.scalar(select(Institution).where(Institution.id == tid))
            if not target_inst:
                raise ValueError(f"Target institution '{tid}' not found")

        package_info = AVAILABLE_PRICING_PACKAGES.get(pricing_package)
        if not package_info:
            raise ValueError(f"Unknown pricing package '{pricing_package}'")

        if not start_date or not end_date:
            raise ValueError("Campaign start and end dates are required")

        if end_date <= start_date:
            raise ValueError("Campaign end date must be strictly after start date")

        campaign = PromotionCampaign(
            source_institution_id=source_institution_id,
            creator_user_id=creator_user_id,
            opportunity_id=opportunity_id,
            target_institution_ids=target_institution_ids,
            campaign_type=campaign_type,
            pricing_package=pricing_package,
            price_amount=package_info["price_amount"],
            currency=package_info["currency"],
            start_date=start_date,
            end_date=end_date,
            status=CampaignStatus.DRAFT,
            is_paid_placement=True,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def review_campaign(
        db: Session,
        campaign_id: str,
        reviewer_user_id: str,
        action: str,  # "approve" | "reject"
        review_notes: str | None = None,
    ) -> PromotionCampaign:
        campaign = db.scalar(select(PromotionCampaign).where(PromotionCampaign.id == campaign_id))
        if not campaign:
            raise LookupError("Promotion campaign not found")

        now = utcnow()
        if action == "approve":
            # If dates align with current time, make active, else scheduled/approved
            if campaign.start_date <= now <= campaign.end_date:
                new_status = CampaignStatus.ACTIVE
            elif campaign.start_date > now:
                new_status = CampaignStatus.SCHEDULED
            else:
                new_status = CampaignStatus.APPROVED

            campaign.status = new_status
        elif action == "reject":
            campaign.status = CampaignStatus.REJECTED
        else:
            raise ValueError(f"Invalid review action '{action}'")

        campaign.reviewer_user_id = reviewer_user_id
        campaign.review_notes = review_notes
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def list_campaigns_for_institution(
        db: Session,
        institution_id: str,
    ) -> list[PromotionCampaign]:
        stmt = (
            select(PromotionCampaign)
            .where(PromotionCampaign.source_institution_id == institution_id)
            .order_by(PromotionCampaign.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_promoted_feed(
        db: Session,
        target_institution_id: str,
    ) -> list[FeedPromotionItem]:
        """Fetch active cross-college sponsored campaigns targeting this institution."""
        now = utcnow()
        stmt = (
            select(PromotionCampaign)
            .where(
                PromotionCampaign.status.in_(
                    [CampaignStatus.ACTIVE, CampaignStatus.APPROVED, CampaignStatus.SCHEDULED]
                ),
                PromotionCampaign.start_date <= now,
                PromotionCampaign.end_date >= now,
            )
            .order_by(PromotionCampaign.created_at.desc())
        )
        campaigns = list(db.scalars(stmt).all())
        feed_items: list[FeedPromotionItem] = []

        for camp in campaigns:
            if target_institution_id in camp.target_institution_ids:
                opp = db.scalar(select(Opportunity).where(Opportunity.id == camp.opportunity_id))
                source_inst = db.scalar(
                    select(Institution).where(Institution.id == camp.source_institution_id)
                )
                if opp and source_inst:
                    feed_items.append(
                        FeedPromotionItem(
                            campaign_id=camp.id,
                            opportunity_id=opp.id,
                            opportunity_title=opp.title or "Untitled Opportunity",
                            opportunity_url=opp.location or opp.id,
                            source_institution_id=source_inst.id,
                            source_institution_name=source_inst.name,
                            campaign_type=camp.campaign_type,
                            sponsored_label="Featured — Sponsored",
                            is_paid_placement=True,
                            start_date=camp.start_date,
                            end_date=camp.end_date,
                        )
                    )
        return feed_items
