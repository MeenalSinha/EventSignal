/**
 * Service for Phase 8: Sponsorship Facilitation, Cross-College Promotion,
 * Alumni CSV Import, and Pilot Evaluation Metrics.
 */

import type {
  AlumniImportJob,
  AlumniImportPreviewResponse,
  FeedPromotionItem,
  PartnerOrganization,
  PilotMetrics,
  PricingPackage,
  PromotionCampaign,
  SponsorshipRequest,
  SponsorshipStatus,
} from "../types/phase8";
import { requestJson } from "./apiClient";
import { getAuthHeaders } from "./authService";

function makeHeaders(institutionId: string): Record<string, string> {
  return {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
}

// ---------------------------------------------------------------------------
// Pricing Packages
// ---------------------------------------------------------------------------

export async function fetchPricingPackages(): Promise<PricingPackage[]> {
  const res = await requestJson("/api/v1/campaigns/pricing-packages");
  return res.body as PricingPackage[];
}

// ---------------------------------------------------------------------------
// Partner Organizations
// ---------------------------------------------------------------------------

export async function fetchPartners(institutionId: string): Promise<PartnerOrganization[]> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/partners`, {
    headers: makeHeaders(institutionId),
  });
  return res.body as PartnerOrganization[];
}

export async function createPartner(
  institutionId: string,
  payload: {
    name: string;
    industry?: string;
    contact_name?: string;
    contact_email?: string;
    website_url?: string;
    verification_status?: string;
    notes?: string;
  }
): Promise<PartnerOrganization> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/partners`, {
    method: "POST",
    headers: makeHeaders(institutionId),
    body: payload,
  });
  return res.body as PartnerOrganization;
}

// ---------------------------------------------------------------------------
// Sponsorship Requests
// ---------------------------------------------------------------------------

export async function fetchSponsorships(
  institutionId: string,
  status?: SponsorshipStatus
): Promise<SponsorshipRequest[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/sponsorships${query}`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  return res.body as SponsorshipRequest[];
}

export async function createSponsorship(
  institutionId: string,
  payload: {
    objective: string;
    proposed_benefits: string;
    opportunity_id?: string;
    partner_organization_id?: string;
    support_type?: string;
    intended_audience?: string;
    budget_currency?: string;
    budget_amount?: number;
    deadline?: string;
    contact_email?: string;
    commercial_terms?: Record<string, unknown>;
  }
): Promise<SponsorshipRequest> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/sponsorships`, {
    method: "POST",
    headers: makeHeaders(institutionId),
    body: payload,
  });
  return res.body as SponsorshipRequest;
}

export async function updateSponsorshipStatus(
  institutionId: string,
  requestId: string,
  status: SponsorshipStatus,
  commercialTerms?: Record<string, unknown>
): Promise<SponsorshipRequest> {
  const res = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/sponsorships/${encodeURIComponent(requestId)}/status`,
    {
      method: "PATCH",
      headers: makeHeaders(institutionId),
      body: { status, commercial_terms: commercialTerms },
    }
  );
  return res.body as SponsorshipRequest;
}

// ---------------------------------------------------------------------------
// Cross-College Promotion Campaigns
// ---------------------------------------------------------------------------

export async function fetchCampaigns(institutionId: string): Promise<PromotionCampaign[]> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/campaigns`, {
    headers: makeHeaders(institutionId),
  });
  return res.body as PromotionCampaign[];
}

export async function createCampaign(
  institutionId: string,
  payload: {
    opportunity_id: string;
    target_institution_ids: string[];
    campaign_type?: string;
    pricing_package?: string;
    start_date: string;
    end_date: string;
  }
): Promise<PromotionCampaign> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/campaigns`, {
    method: "POST",
    headers: makeHeaders(institutionId),
    body: payload,
  });
  return res.body as PromotionCampaign;
}

export async function reviewCampaign(
  institutionId: string,
  campaignId: string,
  action: "approve" | "reject",
  reviewNotes?: string
): Promise<PromotionCampaign> {
  const res = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/campaigns/${encodeURIComponent(campaignId)}/review`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: { action, review_notes: reviewNotes },
    }
  );
  return res.body as PromotionCampaign;
}

export async function fetchPromotedFeed(institutionId: string): Promise<FeedPromotionItem[]> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/campaigns/feed`, {
    headers: makeHeaders(institutionId),
  });
  return res.body as FeedPromotionItem[];
}

// ---------------------------------------------------------------------------
// Alumni Directory CSV Import
// ---------------------------------------------------------------------------

export async function previewAlumniImport(
  institutionId: string,
  filename: string,
  csvText: string
): Promise<AlumniImportPreviewResponse> {
  const res = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/alumni-import/preview`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: { filename, csv_text: csvText },
    }
  );
  return res.body as AlumniImportPreviewResponse;
}

export async function commitAlumniImport(
  institutionId: string,
  filename: string,
  csvText: string
): Promise<AlumniImportJob> {
  const res = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/alumni-import/commit`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: { filename, csv_text: csvText },
    }
  );
  return res.body as AlumniImportJob;
}

export async function fetchAlumniImportJobs(institutionId: string): Promise<AlumniImportJob[]> {
  const res = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/alumni-import/jobs`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  return res.body as AlumniImportJob[];
}

// ---------------------------------------------------------------------------
// Pilot & Release Operational Metrics
// ---------------------------------------------------------------------------

export async function fetchPilotMetrics(institutionId: string): Promise<PilotMetrics> {
  const res = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/pilot-metrics`, {
    headers: makeHeaders(institutionId),
  });
  return res.body as PilotMetrics;
}
