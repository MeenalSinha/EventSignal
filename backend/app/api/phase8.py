"""Phase 8 API router: Partnerships, Cross-College Promotion, Pilot & Release.

Implements:
1. Sponsorship facilitation & partner organization tracking.
2. Cross-college promotion campaigns with transparent disclosures.
3. Approved alumni CSV batch import with zero default consent.
4. Pilot & release evaluation metrics from real persisted data.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    require_institution_admin_access,
    require_institution_membership,
)
from app.database import get_db
from app.models.alumni_import import AlumniImportJob
from app.models.sponsorship import SponsorshipStatus
from app.models.user import User
from app.schemas.phase8 import (
    AlumniImportCommitRequest,
    AlumniImportJobRead,
    AlumniImportPreviewRequest,
    AlumniImportPreviewResponse,
    FeedPromotionItem,
    PartnerOrganizationCreate,
    PartnerOrganizationRead,
    PilotMetricsResponse,
    PricingPackageRead,
    PromotionCampaignCreate,
    PromotionCampaignRead,
    PromotionCampaignReview,
    SponsorshipRequestCreate,
    SponsorshipRequestRead,
    SponsorshipStatusUpdate,
)
from app.services.alumni_import import AlumniImportService
from app.services.pilot_metrics import PilotMetricsService
from app.services.promotion import PromotionService
from app.services.sponsorship import SponsorshipService

router = APIRouter(tags=["phase8"])


# ---------------------------------------------------------------------------
# Pricing Packages (Public / Member discovery)
# ---------------------------------------------------------------------------


@router.get(
    "/campaigns/pricing-packages",
    response_model=list[PricingPackageRead],
    summary="List available cross-college promotion pricing packages",
)
def list_pricing_packages() -> list[PricingPackageRead]:
    return PromotionService.get_pricing_packages()


# ---------------------------------------------------------------------------
# Partner Organizations
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/partners",
    response_model=PartnerOrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a partner organization record",
)
def create_partner(
    institution_id: Annotated[str, Path(...)],
    payload: PartnerOrganizationCreate,
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerOrganizationRead:
    partner = SponsorshipService.create_partner(
        db=db,
        institution_id=institution_id,
        name=payload.name,
        industry=payload.industry,
        contact_name=payload.contact_name,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        website_url=payload.website_url,
        verification_status=payload.verification_status,
        notes=payload.notes,
    )
    return PartnerOrganizationRead.model_validate(partner)


@router.get(
    "/institutions/{institution_id}/partners",
    response_model=list[PartnerOrganizationRead],
    summary="List partner organizations for an institution",
)
def list_partners(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PartnerOrganizationRead]:
    partners = SponsorshipService.list_partners(db, institution_id)
    return [PartnerOrganizationRead.model_validate(p) for p in partners]


# ---------------------------------------------------------------------------
# Sponsorship Requests
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/sponsorships",
    response_model=SponsorshipRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sponsorship request prospectus",
)
def create_sponsorship(
    institution_id: Annotated[str, Path(...)],
    payload: SponsorshipRequestCreate,
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> SponsorshipRequestRead:
    try:
        req = SponsorshipService.create_request(
            db=db,
            institution_id=institution_id,
            organizer_user_id=current_user.id,
            objective=payload.objective,
            proposed_benefits=payload.proposed_benefits,
            opportunity_id=payload.opportunity_id,
            partner_organization_id=payload.partner_organization_id,
            support_type=payload.support_type,
            intended_audience=payload.intended_audience,
            budget_currency=payload.budget_currency,
            budget_amount=payload.budget_amount,
            deadline=payload.deadline,
            contact_email=str(payload.contact_email) if payload.contact_email else None,
            commercial_terms=payload.commercial_terms,
        )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SponsorshipRequestRead.model_validate(req)


@router.get(
    "/institutions/{institution_id}/sponsorships",
    response_model=list[SponsorshipRequestRead],
    summary="List sponsorship requests for an institution",
)
def list_sponsorships(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[SponsorshipStatus | None, Query(alias="status")] = None,
) -> list[SponsorshipRequestRead]:
    requests = SponsorshipService.list_requests(db, institution_id, status=status_filter)
    return [SponsorshipRequestRead.model_validate(r) for r in requests]


@router.patch(
    "/institutions/{institution_id}/sponsorships/{request_id}/status",
    response_model=SponsorshipRequestRead,
    summary="Transition sponsorship request status and commercial terms",
)
def update_sponsorship_status(
    institution_id: Annotated[str, Path(...)],
    request_id: Annotated[str, Path(...)],
    payload: SponsorshipStatusUpdate,
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> SponsorshipRequestRead:
    try:
        updated = SponsorshipService.transition_status(
            db=db,
            institution_id=institution_id,
            request_id=request_id,
            new_status=payload.status,
            commercial_terms=payload.commercial_terms,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SponsorshipRequestRead.model_validate(updated)


# ---------------------------------------------------------------------------
# Cross-College Promotion Campaigns
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/campaigns",
    response_model=PromotionCampaignRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a cross-college promotion campaign",
)
def create_campaign(
    institution_id: Annotated[str, Path(...)],
    payload: PromotionCampaignCreate,
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> PromotionCampaignRead:
    try:
        camp = PromotionService.create_campaign(
            db=db,
            source_institution_id=institution_id,
            creator_user_id=current_user.id,
            opportunity_id=payload.opportunity_id,
            target_institution_ids=payload.target_institution_ids,
            campaign_type=payload.campaign_type,
            pricing_package=payload.pricing_package,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PromotionCampaignRead.model_validate(camp)


@router.get(
    "/institutions/{institution_id}/campaigns",
    response_model=list[PromotionCampaignRead],
    summary="List cross-college campaigns created by this institution",
)
def list_campaigns(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PromotionCampaignRead]:
    camps = PromotionService.list_campaigns_for_institution(db, institution_id)
    return [PromotionCampaignRead.model_validate(c) for c in camps]


@router.post(
    "/institutions/{institution_id}/campaigns/{campaign_id}/review",
    response_model=PromotionCampaignRead,
    summary="Review (approve or reject) a cross-college campaign",
)
def review_campaign(
    institution_id: Annotated[str, Path(...)],
    campaign_id: Annotated[str, Path(...)],
    payload: PromotionCampaignReview,
    current_user: Annotated[User, Depends(require_institution_admin_access)],
    db: Annotated[Session, Depends(get_db)],
) -> PromotionCampaignRead:
    try:
        camp = PromotionService.review_campaign(
            db=db,
            campaign_id=campaign_id,
            reviewer_user_id=current_user.id,
            action=payload.action,
            review_notes=payload.review_notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PromotionCampaignRead.model_validate(camp)


@router.get(
    "/institutions/{institution_id}/campaigns/feed",
    response_model=list[FeedPromotionItem],
    summary="Get cross-college sponsored opportunities targeted at this college",
)
def get_promoted_feed(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> list[FeedPromotionItem]:
    return PromotionService.get_promoted_feed(db, institution_id)


# ---------------------------------------------------------------------------
# Approved Alumni CSV Import
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/alumni-import/preview",
    response_model=AlumniImportPreviewResponse,
    summary="Dry-run preview of an alumni directory CSV upload",
)
def preview_alumni_import(
    institution_id: Annotated[str, Path(...)],
    payload: AlumniImportPreviewRequest,
    current_user: Annotated[User, Depends(require_institution_admin_access)],
    db: Annotated[Session, Depends(get_db)],
) -> AlumniImportPreviewResponse:
    return AlumniImportService.preview(
        db=db,
        institution_id=institution_id,
        filename=payload.filename,
        csv_text=payload.csv_text,
    )


@router.post(
    "/institutions/{institution_id}/alumni-import/commit",
    response_model=AlumniImportJobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Commit validated alumni CSV directory import",
)
def commit_alumni_import(
    institution_id: Annotated[str, Path(...)],
    payload: AlumniImportCommitRequest,
    current_user: Annotated[User, Depends(require_institution_admin_access)],
    db: Annotated[Session, Depends(get_db)],
) -> AlumniImportJobRead:
    return AlumniImportService.commit_import(
        db=db,
        institution_id=institution_id,
        uploader_user_id=current_user.id,
        filename=payload.filename,
        csv_text=payload.csv_text,
    )


@router.get(
    "/institutions/{institution_id}/alumni-import/jobs",
    response_model=list[AlumniImportJobRead],
    summary="List alumni import jobs and audit trail",
)
def list_alumni_import_jobs(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(require_institution_admin_access)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AlumniImportJobRead]:
    stmt = (
        select(AlumniImportJob)
        .where(AlumniImportJob.institution_id == institution_id)
        .order_by(AlumniImportJob.created_at.desc())
    )
    jobs = list(db.scalars(stmt).all())
    return [AlumniImportJobRead.model_validate(j) for j in jobs]


# ---------------------------------------------------------------------------
# Pilot & Release Operational Metrics
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/pilot-metrics",
    response_model=PilotMetricsResponse,
    summary="Retrieve observable pilot operational metrics from real database records",
)
def get_pilot_metrics(
    institution_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    db: Annotated[Session, Depends(get_db)],
) -> PilotMetricsResponse:
    try:
        return PilotMetricsService.calculate_metrics(db, institution_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
