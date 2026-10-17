"""Pydantic schemas for Phase 8: Partnerships, Cross-College Promotion, Pilot & Release."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.alumni_import import ImportJobStatus
from app.models.promotion_campaign import CampaignStatus, CampaignType
from app.models.sponsorship import (
    PartnerVerificationStatus,
    SponsorshipStatus,
    SupportType,
)

# ---------------------------------------------------------------------------
# Partner Organizations
# ---------------------------------------------------------------------------


class PartnerOrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    industry: str | None = Field(None, max_length=100)
    contact_name: str | None = Field(None, max_length=255)
    contact_email: EmailStr | None = None
    website_url: str | None = Field(None, max_length=500)
    verification_status: PartnerVerificationStatus = PartnerVerificationStatus.UNVERIFIED
    notes: str | None = None


class PartnerOrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    industry: str | None = Field(None, max_length=100)
    contact_name: str | None = Field(None, max_length=255)
    contact_email: EmailStr | None = None
    website_url: str | None = Field(None, max_length=500)
    verification_status: PartnerVerificationStatus | None = None
    notes: str | None = None


class PartnerOrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    name: str
    industry: str | None
    contact_name: str | None
    contact_email: str | None
    website_url: str | None
    verification_status: PartnerVerificationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Sponsorship Requests
# ---------------------------------------------------------------------------


class SponsorshipRequestCreate(BaseModel):
    objective: str = Field(..., min_length=3, max_length=255)
    proposed_benefits: str = Field(..., min_length=10)
    opportunity_id: str | None = None
    partner_organization_id: str | None = None
    support_type: SupportType = SupportType.FINANCIAL
    intended_audience: str | None = Field(None, max_length=255)
    budget_currency: str = Field("USD", min_length=3, max_length=3)
    budget_amount: float | None = Field(None, ge=0)
    deadline: datetime | None = None
    contact_email: EmailStr | None = None
    commercial_terms: dict[str, Any] | None = None


class SponsorshipRequestUpdate(BaseModel):
    objective: str | None = Field(None, min_length=3, max_length=255)
    proposed_benefits: str | None = Field(None, min_length=10)
    opportunity_id: str | None = None
    partner_organization_id: str | None = None
    support_type: SupportType | None = None
    intended_audience: str | None = None
    budget_currency: str | None = None
    budget_amount: float | None = Field(None, ge=0)
    deadline: datetime | None = None
    contact_email: EmailStr | None = None
    commercial_terms: dict[str, Any] | None = None


class SponsorshipStatusUpdate(BaseModel):
    status: SponsorshipStatus
    commercial_terms: dict[str, Any] | None = None


class SponsorshipRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    opportunity_id: str | None
    organizer_user_id: str
    partner_organization_id: str | None
    objective: str
    support_type: SupportType
    proposed_benefits: str
    intended_audience: str | None
    budget_currency: str
    budget_amount: float | None
    deadline: datetime | None
    contact_email: str | None
    status: SponsorshipStatus
    commercial_terms: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Cross-College Promotion Campaigns
# ---------------------------------------------------------------------------


class PricingPackageRead(BaseModel):
    package_id: str
    name: str
    description: str
    price_amount: float
    currency: str
    duration_days: int
    placement_type: str


class PromotionCampaignCreate(BaseModel):
    opportunity_id: str
    target_institution_ids: list[str] = Field(..., min_length=1)
    campaign_type: CampaignType = CampaignType.FEATURED_SPOTLIGHT
    pricing_package: str = "standard_cross_college"
    start_date: datetime
    end_date: datetime


class PromotionCampaignReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    review_notes: str | None = None


class PromotionCampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_institution_id: str
    opportunity_id: str
    creator_user_id: str
    target_institution_ids: list[str]
    campaign_type: CampaignType
    pricing_package: str
    price_amount: float | None
    currency: str
    start_date: datetime
    end_date: datetime
    status: CampaignStatus
    reviewer_user_id: str | None
    review_notes: str | None
    is_paid_placement: bool
    sponsored_label: str = "Featured — Sponsored"
    created_at: datetime
    updated_at: datetime


class FeedPromotionItem(BaseModel):
    campaign_id: str
    opportunity_id: str
    opportunity_title: str
    opportunity_url: str | None = None
    source_institution_id: str
    source_institution_name: str
    campaign_type: CampaignType
    sponsored_label: str = "Featured — Sponsored"
    is_paid_placement: bool = True
    start_date: datetime
    end_date: datetime


# ---------------------------------------------------------------------------
# Approved Alumni CSV Import
# ---------------------------------------------------------------------------


class AlumniImportPreviewRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    csv_text: str = Field(..., min_length=5)


class AlumniImportRowPreview(BaseModel):
    row_number: int
    full_name: str
    email: str
    grad_year: int | None = None
    degree: str | None = None
    current_role: str | None = None
    company: str | None = None
    is_duplicate: bool = False
    validation_error: str | None = None


class AlumniImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    duplicate_rows: int
    invalid_rows: int
    preview_records: list[AlumniImportRowPreview]
    consent_notice: str = (
        "Notice: Imported alumni identities are created with pending consent and private "
        "visibility. Mentorship and connection requests remain disabled until explicitly "
        "opted-in by the user."
    )


class AlumniImportCommitRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    csv_text: str = Field(..., min_length=5)


class AlumniImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    uploader_user_id: str
    filename: str
    status: ImportJobStatus
    total_rows: int
    accepted_rows: int
    skipped_rows: int
    rejected_rows: int
    validation_errors: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Pilot & Release Operational Metrics
# ---------------------------------------------------------------------------


class PilotMetricsResponse(BaseModel):
    institution_id: str
    institution_name: str
    generated_at: datetime
    opportunities: dict[str, int]
    student_needs: dict[str, int]
    helper_matches: dict[str, int]
    legacy_knowledge: dict[str, int]
    sponsorship: dict[str, int]
    cross_college_promotion: dict[str, int]
    alumni_network: dict[str, int]
    readiness_status: str
    notes: list[str]
