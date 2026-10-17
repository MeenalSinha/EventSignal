import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { UserProfile } from "../types/auth";
import type {
  PilotMetrics,
  PricingPackage,
  PromotionCampaign,
  SponsorshipRequest,
} from "../types/phase8";
import { PartnershipsPromotionPanel } from "./PartnershipsPromotionPanel";

const testUser: UserProfile = {
  user: {
    id: "usr-organizer-1",
    email: "organizer@campus.edu",
    full_name: "Bob Organizer",
    is_active: true,
    is_superuser: false,
    created_at: "2026-01-01T00:00:00Z",
  },
  memberships: [
    {
      id: "mem-1",
      institution_id: "inst-1",
      institution_name: "Apex Engineering College",
      institution_slug: "apex-eng",
      role: "admin",
      status: "active",
      joined_at: "2026-01-01T00:00:00Z",
    },
  ],
};

const mockSponsorship: SponsorshipRequest = {
  id: "spon-1",
  institution_id: "inst-1",
  opportunity_id: "opp-1",
  organizer_user_id: "usr-organizer-1",
  partner_organization_id: null,
  objective: "Seeking cloud credits and prizes for 500 undergraduate engineers.",
  support_type: "financial",
  proposed_benefits: "Keynote speaking slot and banner logo placement.",
  intended_audience: "Computer Science and Electrical Engineering juniors and seniors.",
  budget_currency: "INR",
  budget_amount: 50000,
  deadline: "2026-11-01T00:00:00Z",
  contact_email: "sponsor-desk@apex.edu",
  status: "under_review",
  commercial_terms: null,
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-02T00:00:00Z",
};

const mockCampaign: PromotionCampaign = {
  id: "camp-1",
  source_institution_id: "inst-1",
  opportunity_id: "opp-1",
  creator_user_id: "usr-organizer-1",
  target_institution_ids: ["inst-2"],
  campaign_type: "cross_college_banner",
  pricing_package: "standard_cross_college",
  price_amount: 2500,
  currency: "INR",
  start_date: "2026-10-15T00:00:00Z",
  end_date: "2026-11-15T00:00:00Z",
  status: "approved",
  reviewer_user_id: "usr-admin-1",
  review_notes: "Approved for inter-college display.",
  is_paid_placement: true,
  sponsored_label: "Featured — Sponsored",
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-02T00:00:00Z",
};

const mockPricingPackages: PricingPackage[] = [
  {
    package_id: "standard_cross_college",
    name: "Standard Cross-College Placement",
    description: "Featured promotion on 1 partner college event feed for 14 days.",
    price_amount: 2500,
    currency: "INR",
    duration_days: 14,
    placement_type: "target_college_feed",
  },
];

const mockMetrics: PilotMetrics = {
  institution_id: "inst-1",
  institution_name: "Apex Engineering College",
  generated_at: "2026-10-18T00:00:00Z",
  opportunities: {
    total: 12,
    assessed: 10,
    high_evidence: 8,
    moderate_evidence: 2,
    low_evidence: 0,
  },
  student_needs: {
    total: 8,
    open: 4,
    matched: 3,
    resolved: 1,
  },
  helper_matches: {
    total_evaluated: 14,
    accepted: 4,
    pending: 2,
    dismissed: 1,
  },
  legacy_knowledge: {
    handovers_total: 3,
    handovers_acknowledged: 3,
    memories_total: 5,
    tasks_total: 7,
    tasks_completed: 4,
  },
  sponsorship: {
    requests_total: 2,
    draft: 0,
    submitted: 0,
    under_review: 2,
    accepted: 0,
    declined: 0,
    closed: 0,
  },
  cross_college_promotion: {
    campaigns_created: 1,
    campaigns_approved: 1,
    campaigns_active: 1,
  },
  alumni_network: {
    total_members: 45,
    student_count: 30,
    alumni_count: 15,
    import_jobs_count: 1,
    imported_rows_accepted: 15,
  },
  readiness_status: "READY_FOR_PILOT",
  notes: ["Healthy evidence assessment and active alumni mentoring network."],
};

describe("PartnershipsPromotionPanel", () => {
  it("renders prompt to sign in when no user is logged in", () => {
    const onOpenAuth = vi.fn();
    render(<PartnershipsPromotionPanel currentUser={null} onOpenAuth={onOpenAuth} />);
    expect(
      screen.getByText("Sign in to Access Partnerships & Promotion")
    ).toBeInTheDocument();
  });

  it("renders sponsorship prospectuses and switches through all Phase 8 subtabs", async () => {
    stubFetch({
      "/api/v1/institutions/inst-1/partners": () => jsonResponse([]),
      "/api/v1/institutions/inst-1/sponsorships": () => jsonResponse([mockSponsorship]),
      "/api/v1/campaigns/pricing-packages": () => jsonResponse(mockPricingPackages),
      "/api/v1/institutions/inst-1/campaigns": () => jsonResponse([mockCampaign]),
      "/api/v1/institutions/inst-1/campaigns/feed": () => jsonResponse([]),
      "/api/v1/institutions/inst-1/alumni-import/jobs": () => jsonResponse([]),
      "/api/v1/institutions/inst-1/pilot-metrics": () => jsonResponse(mockMetrics),
      "/api/v1/events": () => jsonResponse({ items: [], total: 0 }),
      "/api/v1/institutions": () => jsonResponse({ items: [], total: 0 }),
    });

    render(<PartnershipsPromotionPanel currentUser={testUser} onOpenAuth={() => {}} />);

    // Verify workspace header
    expect(await screen.findByText(/Apex Engineering College/i)).toBeInTheDocument();

    // Verify subtab navigation
    expect(screen.getByText(/Sponsorships \(/i)).toBeInTheDocument();
    expect(screen.getByText(/Cross-College Promotion/i)).toBeInTheDocument();
    expect(screen.getByText(/Alumni CSV Import/i)).toBeInTheDocument();
    expect(screen.getByText(/Pilot Analytics/i)).toBeInTheDocument();

    // Verify sponsorship request is rendered
    expect(
      await screen.findByText("Seeking cloud credits and prizes for 500 undergraduate engineers.")
    ).toBeInTheDocument();
    expect(screen.getByText(/INR 50,000/i)).toBeInTheDocument();

    const user = userEvent.setup();

    // Switch to Cross-College Promotion subtab
    await user.click(screen.getByText(/Cross-College Promotion/i));
    expect(await screen.findByText("Standard Cross-College Placement")).toBeInTheDocument();

    // Switch to Alumni Directory Import subtab
    await user.click(screen.getByText(/Alumni CSV Import/i));
    expect(
      await screen.findByText("Approved Alumni CSV Directory Import")
    ).toBeInTheDocument();
    expect(screen.getByText("Upload or Paste CSV Directory Data")).toBeInTheDocument();

    // Switch to Pilot & Release Metrics subtab
    await user.click(screen.getByText(/Pilot Analytics/i));
    expect(
      await screen.findByText("Pilot & Release Operational Metrics")
    ).toBeInTheDocument();
    expect(screen.getByText("READY FOR PILOT")).toBeInTheDocument();
  });
});
