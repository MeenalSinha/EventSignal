"""Sponsorship and partner management service for EventSignal Phase 8.

Enforces institutional isolation, state machine transitions, and transparent
commercial tracking without automated payment processing or fabricated interest.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.opportunity import Opportunity
from app.models.sponsorship import (
    PartnerOrganization,
    PartnerVerificationStatus,
    SponsorshipRequest,
    SponsorshipStatus,
    SupportType,
)

VALID_SPONSORSHIP_TRANSITIONS: dict[SponsorshipStatus, set[SponsorshipStatus]] = {
    SponsorshipStatus.DRAFT: {SponsorshipStatus.SUBMITTED, SponsorshipStatus.WITHDRAWN},
    SponsorshipStatus.SUBMITTED: {
        SponsorshipStatus.UNDER_REVIEW,
        SponsorshipStatus.DECLINED,
        SponsorshipStatus.WITHDRAWN,
    },
    SponsorshipStatus.UNDER_REVIEW: {
        SponsorshipStatus.ACCEPTED,
        SponsorshipStatus.DECLINED,
        SponsorshipStatus.WITHDRAWN,
    },
    SponsorshipStatus.ACCEPTED: {SponsorshipStatus.CLOSED, SponsorshipStatus.WITHDRAWN},
    SponsorshipStatus.DECLINED: set(),
    SponsorshipStatus.CLOSED: set(),
    SponsorshipStatus.WITHDRAWN: set(),
}


class SponsorshipService:
    @staticmethod
    def create_partner(
        db: Session,
        institution_id: str,
        name: str,
        industry: str | None = None,
        contact_name: str | None = None,
        contact_email: str | None = None,
        website_url: str | None = None,
        verification_status: PartnerVerificationStatus = PartnerVerificationStatus.UNVERIFIED,
        notes: str | None = None,
    ) -> PartnerOrganization:
        partner = PartnerOrganization(
            institution_id=institution_id,
            name=name.strip(),
            industry=industry.strip() if industry else None,
            contact_name=contact_name.strip() if contact_name else None,
            contact_email=contact_email.strip() if contact_email else None,
            website_url=website_url.strip() if website_url else None,
            verification_status=verification_status,
            notes=notes.strip() if notes else None,
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
        return partner

    @staticmethod
    def list_partners(
        db: Session,
        institution_id: str,
    ) -> list[PartnerOrganization]:
        stmt = (
            select(PartnerOrganization)
            .where(PartnerOrganization.institution_id == institution_id)
            .order_by(PartnerOrganization.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_request(
        db: Session,
        institution_id: str,
        organizer_user_id: str,
        objective: str,
        proposed_benefits: str,
        opportunity_id: str | None = None,
        partner_organization_id: str | None = None,
        support_type: SupportType = SupportType.FINANCIAL,
        intended_audience: str | None = None,
        budget_currency: str = "USD",
        budget_amount: float | None = None,
        deadline: Any | None = None,
        contact_email: str | None = None,
        commercial_terms: dict[str, Any] | None = None,
    ) -> SponsorshipRequest:
        if opportunity_id:
            opp = db.scalar(select(Opportunity).where(Opportunity.id == opportunity_id))
            if not opp:
                raise ValueError("Referenced opportunity does not exist")

        if partner_organization_id:
            partner = db.scalar(
                select(PartnerOrganization).where(
                    PartnerOrganization.id == partner_organization_id,
                    PartnerOrganization.institution_id == institution_id,
                )
            )
            if not partner:
                raise ValueError(
                    "Referenced partner organization does not exist in this institution"
                )

        request = SponsorshipRequest(
            institution_id=institution_id,
            organizer_user_id=organizer_user_id,
            opportunity_id=opportunity_id,
            partner_organization_id=partner_organization_id,
            objective=objective.strip(),
            proposed_benefits=proposed_benefits.strip(),
            support_type=support_type,
            intended_audience=intended_audience.strip() if intended_audience else None,
            budget_currency=budget_currency.upper(),
            budget_amount=budget_amount,
            deadline=deadline,
            contact_email=contact_email.strip() if contact_email else None,
            status=SponsorshipStatus.DRAFT,
            commercial_terms=commercial_terms or {},
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def transition_status(
        db: Session,
        institution_id: str,
        request_id: str,
        new_status: SponsorshipStatus,
        commercial_terms: dict[str, Any] | None = None,
    ) -> SponsorshipRequest:
        stmt = select(SponsorshipRequest).where(
            SponsorshipRequest.id == request_id,
            SponsorshipRequest.institution_id == institution_id,
        )
        req = db.scalar(stmt)
        if not req:
            raise LookupError("Sponsorship request not found")

        current_status = req.status
        allowed = VALID_SPONSORSHIP_TRANSITIONS.get(current_status, set())
        if new_status not in allowed and new_status != current_status:
            raise ValueError(f"Invalid status transition from '{current_status}' to '{new_status}'")

        req.status = new_status
        if commercial_terms:
            existing_terms = dict(req.commercial_terms or {})
            existing_terms.update(commercial_terms)
            req.commercial_terms = existing_terms
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(req, "commercial_terms")

        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def list_requests(
        db: Session,
        institution_id: str,
        status: SponsorshipStatus | None = None,
    ) -> list[SponsorshipRequest]:
        stmt = select(SponsorshipRequest).where(SponsorshipRequest.institution_id == institution_id)
        if status:
            stmt = stmt.where(SponsorshipRequest.status == status)
        stmt = stmt.order_by(SponsorshipRequest.created_at.desc())
        return list(db.scalars(stmt).all())
