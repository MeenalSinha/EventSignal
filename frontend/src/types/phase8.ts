export type SponsorshipStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "accepted"
  | "declined"
  | "closed"
  | "withdrawn";

export type SupportType =
  | "financial"
  | "in_kind"
  | "mentorship"
  | "venue"
  | "swag"
  | "other";

export type PartnerVerificationStatus =
  | "unverified"
  | "expressed_interest"
  | "verified_representative"
  | "confirmed_sponsor";

export interface PartnerOrganization {
  id: string;
  institution_id: string;
  name: string;
  industry: string | null;
  contact_name: string | null;
  contact_email: string | null;
  website_url: string | null;
  verification_status: PartnerVerificationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SponsorshipRequest {
  id: string;
  institution_id: string;
  opportunity_id: string | null;
  organizer_user_id: string;
  partner_organization_id: string | null;
  objective: string;
  support_type: SupportType;
  proposed_benefits: string;
  intended_audience: string | null;
  budget_currency: string;
  budget_amount: number | null;
  deadline: string | null;
  contact_email: string | null;
  status: SponsorshipStatus;
  commercial_terms: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export type CampaignStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "approved"
  | "scheduled"
  | "active"
  | "completed"
  | "rejected"
  | "cancelled";

export type CampaignType =
  | "featured_spotlight"
  | "campus_bulletin"
  | "cross_college_banner";

export interface PricingPackage {
  package_id: string;
  name: string;
  description: string;
  price_amount: number;
  currency: string;
  duration_days: number;
  placement_type: string;
}

export interface PromotionCampaign {
  id: string;
  source_institution_id: string;
  opportunity_id: string;
  creator_user_id: string;
  target_institution_ids: string[];
  campaign_type: CampaignType;
  pricing_package: string;
  price_amount: number | null;
  currency: string;
  start_date: string;
  end_date: string;
  status: CampaignStatus;
  reviewer_user_id: string | null;
  review_notes: string | null;
  is_paid_placement: boolean;
  sponsored_label: string;
  created_at: string;
  updated_at: string;
}

export interface FeedPromotionItem {
  campaign_id: string;
  opportunity_id: string;
  opportunity_title: string;
  opportunity_url: string | null;
  source_institution_id: string;
  source_institution_name: string;
  campaign_type: CampaignType;
  sponsored_label: string;
  is_paid_placement: boolean;
  start_date: string;
  end_date: string;
}

export interface AlumniImportRowPreview {
  row_number: number;
  full_name: string;
  email: string;
  grad_year: number | null;
  degree: string | null;
  current_role: string | null;
  company: string | null;
  is_duplicate: boolean;
  validation_error: string | null;
}

export interface AlumniImportPreviewResponse {
  filename: string;
  total_rows: number;
  valid_rows: number;
  duplicate_rows: number;
  invalid_rows: number;
  preview_records: AlumniImportRowPreview[];
  consent_notice: string;
}

export interface AlumniImportJob {
  id: string;
  institution_id: string;
  uploader_user_id: string;
  filename: string;
  status: "preview" | "committed" | "failed";
  total_rows: number;
  accepted_rows: number;
  skipped_rows: number;
  rejected_rows: number;
  validation_errors: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

export interface PilotMetrics {
  institution_id: string;
  institution_name: string;
  generated_at: string;
  opportunities: {
    total: number;
    assessed: number;
    high_evidence: number;
    moderate_evidence: number;
    low_evidence: number;
  };
  student_needs: {
    total: number;
    open: number;
    matched: number;
    resolved: number;
  };
  helper_matches: {
    total_evaluated: number;
    accepted: number;
    pending: number;
    dismissed: number;
  };
  legacy_knowledge: {
    handovers_total: number;
    handovers_acknowledged: number;
    memories_total: number;
    tasks_total: number;
    tasks_completed: number;
  };
  sponsorship: {
    requests_total: number;
    draft: number;
    submitted: number;
    under_review: number;
    accepted: number;
    declined: number;
    closed: number;
  };
  cross_college_promotion: {
    campaigns_created: number;
    campaigns_approved: number;
    campaigns_active: number;
  };
  alumni_network: {
    total_members: number;
    student_count: number;
    alumni_count: number;
    import_jobs_count: number;
    imported_rows_accepted: number;
  };
  readiness_status: string;
  notes: string[];
}
