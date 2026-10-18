import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { UserProfile } from "../types/auth";
import type { HelpOffer, HelpOfferListResponse } from "../types/helpOffer";
import { HelpOffersPanel } from "./HelpOffersPanel";

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

const mockOffer: HelpOffer = {
  id: "offer-1",
  institution_id: "inst-1",
  user_id: "usr-alumni-1",
  title: "Mock Technical Interview Practice",
  category: "Mock Interviews",
  description: "1-on-1 practice interviews with feedback on data structures and system design.",
  topics: ["Algorithms", "System Design"],
  target_audience: "all_students",
  delivery_mode: "virtual",
  capacity_per_month: 4,
  status: "active",
  creator_name: "Bob Alumnus",
  creator_role: "alumni",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockListResponse: HelpOfferListResponse = {
  total: 1,
  items: [mockOffer],
  categories: ["Mock Interviews", "Portfolio Reviews"],
};

describe("HelpOffersPanel", () => {
  it("renders active help offers, category filter, and allows requesting help", async () => {
    stubFetch({
      "/api/v1/help-offers/discovery": () => jsonResponse(mockListResponse),
      "/api/v1/help-offers/offer-1/request": () => {
        return jsonResponse({
          id: "req-1",
          institution_id: "inst-1",
          help_offer_id: "offer-1",
          sender_id: "usr-student-1",
          recipient_id: "usr-alumni-1",
          message: "Hi Bob, I'd like to practice mock interviews for HackShift.",
          status: "pending",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        });
      },
    });

    const onOpenAuth = vi.fn();
    render(<HelpOffersPanel currentUser={testUser} onOpenAuth={onOpenAuth} />);

    expect(await screen.findByText("Mock Technical Interview Practice")).toBeInTheDocument();
    expect(screen.getByText(/Offered by/)).toBeInTheDocument();
    expect(screen.getByText("Bob Alumnus")).toBeInTheDocument();
    expect(screen.getByText("virtual")).toBeInTheDocument();
    expect(screen.getAllByText("Mock Interviews").length).toBeGreaterThanOrEqual(1);

    // Click request help
    const requestBtn = screen.getByRole("button", { name: "Request Help" });
    await userEvent.click(requestBtn);

    expect(screen.getByText(/Request Help: Mock Technical Interview Practice/)).toBeInTheDocument();

    const textarea = screen.getByPlaceholderText(/Introduce yourself, explain what specific guidance/);
    await userEvent.type(textarea, "Hi Bob, I would love some interview guidance for my upcoming applications!");

    const sendBtn = screen.getByRole("button", { name: "Send Request" });
    await userEvent.click(sendBtn);

    expect(await screen.findByText(/Your guidance request has been sent to the mentor!/)).toBeInTheDocument();
  });

  it("switches to manage tab and allows publishing new help offer", async () => {
    stubFetch({
      "/api/v1/help-offers/discovery": () => jsonResponse(mockListResponse),
      "/api/v1/help-offers/me": () => jsonResponse([]),
      "/api/v1/help-offers": () => jsonResponse(mockOffer),
    });

    const onOpenAuth = vi.fn();
    render(<HelpOffersPanel currentUser={testUser} onOpenAuth={onOpenAuth} />);

    const manageTabBtn = screen.getByRole("button", { name: /My Published Offers/ });
    await userEvent.click(manageTabBtn);

    expect(await screen.findByText("Publish a Help Offer")).toBeInTheDocument();
    expect(screen.getByText(/You haven't created any help offers/)).toBeInTheDocument();
  });

  it("safely renders without blank screen when categories is omitted or undefined in backend response", async () => {
    // Exact root cause reproduction payload: categories omitted entirely
    const payloadWithoutCategories = {
      items: [mockOffer],
      total: 1,
      limit: 20,
      offset: 0,
    };

    stubFetch({
      "/api/v1/help-offers/discovery": () => jsonResponse(payloadWithoutCategories),
    });

    render(<HelpOffersPanel currentUser={testUser} onOpenAuth={vi.fn()} />);
    expect(await screen.findByText("Mock Technical Interview Practice")).toBeInTheDocument();
    // Verify no crashing and renders offer details
    expect(screen.getByText("Bob Alumnus")).toBeInTheDocument();
  });

  it("shows understandable error state with retry option when help offers API fails", async () => {
    let failed = true;
    stubFetch({
      "/api/v1/help-offers/discovery": () =>
        failed
          ? jsonResponse({ detail: "Gateway timeout" }, 504)
          : jsonResponse(mockListResponse),
    });

    render(<HelpOffersPanel currentUser={testUser} onOpenAuth={vi.fn()} />);
    expect(await screen.findByText(/Failed to load help offers/i)).toBeInTheDocument();
    const retryBtn = screen.getByRole("button", { name: "Retry" });
    expect(retryBtn).toBeInTheDocument();

    failed = false;
    retryBtn.click();
    expect(await screen.findByText("Mock Technical Interview Practice")).toBeInTheDocument();
  });
});
