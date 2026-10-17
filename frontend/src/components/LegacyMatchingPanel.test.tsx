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
});
