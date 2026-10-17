import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { UserProfile } from "../types/auth";
import type { MemberDiscovery } from "../types/profile";
import { MemberDiscoveryPanel } from "./MemberDiscoveryPanel";

const testUser: UserProfile = {
  user: {
    id: "usr-1",
    email: "test@campus.edu",
    full_name: "Test User",
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

const mockMembers: MemberDiscovery[] = [
  {
    user_id: "usr-alumni-1",
    full_name: "Sarah Alum",
    membership_role: "alumni",
    status: "active",
    joined_at: "2026-01-01T00:00:00Z",
    campus_positions: ["Former ACM Chair"],
    student_profile: null,
    alumni_profile: {
      id: "ap-1",
      user_id: "usr-alumni-1",
      institution_id: "inst-1",
      membership_id: "mem-alumni-1",
      current_title: "Product Manager",
      current_organization: "Google",
      professional_domain: "AI Products",
      industry: "Technology",
      years_of_experience: 6,
      skills: ["Product Strategy", "Roadmapping"],
      mentoring_topics: ["Portfolio Reviews", "Career Guidance"],
      bio: "Passionate about helping new graduates.",
      linkedin_url: null,
      website_url: null,
      willing_to_help: true,
      preferred_contact_method: "virtual",
      monthly_request_limit: 4,
      active_requests_this_month: 1,
      visibility: "students_only",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
    active_help_offers_count: 2,
  },
];

describe("MemberDiscoveryPanel", () => {
  it("renders member discovery list with verified campus positions and profile details", async () => {
    stubFetch({
      "/api/v1/profiles/discovery": () => jsonResponse(mockMembers),
    });

    const onOpenAuth = vi.fn();
    render(<MemberDiscoveryPanel currentUser={testUser} onOpenAuth={onOpenAuth} />);

    expect(await screen.findByText("Sarah Alum")).toBeInTheDocument();
    expect(screen.getByText("alumni")).toBeInTheDocument();
    expect(screen.getByText("🎖️ Former ACM Chair")).toBeInTheDocument();
    expect(screen.getByText("Product Manager at Google")).toBeInTheDocument();
    expect(screen.getByText("2 Help Offers")).toBeInTheDocument();
    expect(screen.getByText("Portfolio Reviews")).toBeInTheDocument();
  });

  it("renders sign-in prompt when unauthenticated", () => {
    const onOpenAuth = vi.fn();
    render(<MemberDiscoveryPanel currentUser={null} onOpenAuth={onOpenAuth} />);

    expect(screen.getByText("Campus Network Discovery")).toBeInTheDocument();
    const signinBtn = screen.getByRole("button", { name: "Sign In to Access Network" });
    expect(signinBtn).toBeInTheDocument();
  });

  it("renders truthful empty state when no members match", async () => {
    stubFetch({
      "/api/v1/profiles/discovery": () => jsonResponse([]),
    });

    const onOpenAuth = vi.fn();
    render(<MemberDiscoveryPanel currentUser={testUser} onOpenAuth={onOpenAuth} />);

    expect(await screen.findByText("No Members Found")).toBeInTheDocument();
  });
});
