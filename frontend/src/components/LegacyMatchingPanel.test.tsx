import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { UserProfile } from "../types/auth";
import type { Phase7ListResponse, StudentNeed } from "../types/phase7";
import { LegacyMatchingPanel } from "./LegacyMatchingPanel";

const testUser: UserProfile = {
  user: {
    id: "usr-student-1",
    email: "student@campus.edu",
    full_name: "Alice Student",
    is_active: true,
    is_superuser: false,
    created_at: "2026-01-01T00:00:00Z",
  },
  memberships: [
    {
      id: "mem-1",
      institution_id: "inst-1",
      institution_name: "Tech Institute",
      institution_slug: "tech-inst",
      role: "student",
      status: "active",
      joined_at: "2026-01-01T00:00:00Z",
    },
  ],
};

const mockNeed: StudentNeed = {
  id: "need-1",
  student_profile_id: "sp-1",
  institution_id: "inst-1",
  title: "Mock Interview Help for SWE Placement",
  category: "mock_interview",
  description: "Need practice on data structures and algorithms.",
  preferred_delivery_mode: "remote",
  urgency: "high",
  status: "open",
  extra_data: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockNeedsResponse: Phase7ListResponse<StudentNeed> = {
  items: [mockNeed],
  total: 1,
  limit: 50,
  offset: 0,
};

describe("LegacyMatchingPanel", () => {
  it("renders prompt to sign in when no user is logged in", () => {
    const onOpenAuth = vi.fn();
    render(<LegacyMatchingPanel currentUser={null} onOpenAuth={onOpenAuth} />);
    expect(
      screen.getByText("Sign in to Access Campus Matching & Legacy")
    ).toBeInTheDocument();
  });

  it("renders needs, switches subtabs, and displays declared needs", async () => {
    stubFetch({
      "/api/v1/institutions/inst-1/needs": () => jsonResponse(mockNeedsResponse),
      "/api/v1/institutions/inst-1/needs/need-1/matches": () => jsonResponse([]),
      "/api/v1/institutions/inst-1/handovers": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
      "/api/v1/institutions/inst-1/memories": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
      "/api/v1/institutions/inst-1/tasks": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
    });

    render(<LegacyMatchingPanel currentUser={testUser} onOpenAuth={() => {}} />);

    // Check college workspace name
    expect(screen.getByText(/Tech Institute/i)).toBeInTheDocument();

    // Check subtab buttons
    expect(screen.getByText("Support Needs & Matching")).toBeInTheDocument();
    expect(screen.getByText("Legacy Handovers")).toBeInTheDocument();
    expect(screen.getByText("Event Memories")).toBeInTheDocument();
    expect(screen.getByText("Follow-Up Tasks")).toBeInTheDocument();

    // Check that declared need shows up
    expect(
      await screen.findByText("Mock Interview Help for SWE Placement")
    ).toBeInTheDocument();

    // Switch to Legacy Handovers subtab
    const user = userEvent.setup();
    await user.click(screen.getByText("Legacy Handovers"));
    expect(
      await screen.findByText("Campus Leadership Handovers")
    ).toBeInTheDocument();
  });

  it("safely handles paginated helper match responses { items: [...] } without calling map on an object", async () => {
    const mockMatchPayload = {
      items: [
        {
          id: "match-1",
          need_id: "need-1",
          helper_id: "usr-alumni-1",
          offer_owner_name: "Dr. Evelyn Reed",
          helper_role: "faculty",
          helper_email: "evelyn@campus.edu",
          score: 0.88,
          confidence: "high",
          matched_skills: ["Python", "Algorithms"],
          status: "suggested",
          notes: "Top match for academic SWE preparation",
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    };

    stubFetch({
      "/api/v1/institutions/inst-1/needs": () => jsonResponse(mockNeedsResponse),
      "/api/v1/institutions/inst-1/needs/need-1/matches": () => jsonResponse(mockMatchPayload),
      "/api/v1/institutions/inst-1/handovers": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
      "/api/v1/institutions/inst-1/memories": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
      "/api/v1/institutions/inst-1/tasks": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
    });

    render(<LegacyMatchingPanel currentUser={testUser} onOpenAuth={() => {}} />);
    expect(await screen.findByText("Mock Interview Help for SWE Placement")).toBeInTheDocument();
    expect(await screen.findByText(/Dr\. Evelyn Reed/)).toBeInTheDocument();
    expect(screen.getByText("88%")).toBeInTheDocument();
  });

  it("displays helpful error alert with retry button when needs request fails", async () => {
    let failed = true;
    stubFetch({
      "/api/v1/institutions/inst-1/needs": () =>
        failed
          ? jsonResponse({ detail: "Database unavailable" }, 503)
          : jsonResponse(mockNeedsResponse),
      "/api/v1/institutions/inst-1/handovers": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
      "/api/v1/institutions/inst-1/memories": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
      "/api/v1/institutions/inst-1/tasks": () =>
        jsonResponse({ items: [], total: 0, limit: 50, offset: 0 }),
    });

    render(<LegacyMatchingPanel currentUser={testUser} onOpenAuth={() => {}} />);
    expect(await screen.findByText(/Database unavailable/i)).toBeInTheDocument();
    const retryBtn = screen.getByRole("button", { name: "Retry" });
    expect(retryBtn).toBeInTheDocument();

    failed = false;
    const user = userEvent.setup();
    await user.click(retryBtn);
    expect(await screen.findByText("Mock Interview Help for SWE Placement")).toBeInTheDocument();
  });
});
