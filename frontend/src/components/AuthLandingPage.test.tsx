import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AuthLandingPage } from "./AuthLandingPage";
import App from "../App";
import { emptyEvents, healthBody, jsonResponse, stubFetch } from "../test/helpers";

const HEALTH = "/api/v1/health";
const EVENTS = "/api/v1/events";

describe("AuthLandingPage", () => {
  it("renders the welcoming landing page with branding and headline", () => {
    render(
      <AuthLandingPage
        onAuthSuccess={vi.fn()}
        onContinueAsGuest={vi.fn()}
      />
    );

    expect(screen.getByText("EventSignal")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Your Campus.*Your Opportunities.*Your Network/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Discover verified opportunities, connect with students and alumni mentors/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Continue as Guest \/ Skip for Now/i })
    ).toBeInTheDocument();
  });

  it("switches between Sign In and Register forms", async () => {
    render(
      <AuthLandingPage
        onAuthSuccess={vi.fn()}
        onContinueAsGuest={vi.fn()}
      />
    );

    // Initially on Sign In
    expect(screen.getByRole("button", { name: "Sign In to EventSignal" })).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("e.g., Aanya Sharma")).not.toBeInTheDocument();

    // Click Register button in tab
    await userEvent.click(screen.getByRole("button", { name: "Register" }));
    expect(screen.getByRole("button", { name: "Create Account" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g., Aanya Sharma")).toBeInTheDocument();

    // Toggle show password
    const showPasswordBtn = screen.getByRole("button", { name: "Show password" });
    await userEvent.click(showPasswordBtn);
    expect(screen.getByRole("button", { name: "Hide password" })).toBeInTheDocument();
  });

  it("calls onContinueAsGuest when Skip for Now is clicked", async () => {
    const handleGuest = vi.fn();
    render(
      <AuthLandingPage
        onAuthSuccess={vi.fn()}
        onContinueAsGuest={handleGuest}
      />
    );

    const guestBtn = screen.getByRole("button", { name: /Continue as Guest \/ Skip for Now/i });
    await userEvent.click(guestBtn);
    expect(handleGuest).toHaveBeenCalledTimes(1);
  });
});

describe("App Authentication-First Flow", () => {
  it("renders AuthLandingPage when initialMode is 'landing'", async () => {
    stubFetch({
      [HEALTH]: () => jsonResponse(healthBody()),
      [EVENTS]: () => jsonResponse(emptyEvents),
    });

    render(<App initialMode="landing" />);
    expect(
      screen.getByRole("heading", { name: /Your Campus.*Your Opportunities.*Your Network/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Continue as Guest / Skip for Now" })
    ).toBeInTheDocument();
  });

  it("transitions into guest dashboard when visitor skips landing page", async () => {
    stubFetch({
      [HEALTH]: () => jsonResponse(healthBody()),
      [EVENTS]: () => jsonResponse(emptyEvents),
    });

    render(<App initialMode="landing" />);
    const guestBtn = screen.getByRole("button", { name: /Continue as Guest \/ Skip for Now/i });
    await userEvent.click(guestBtn);

    // Now in the guest dashboard
    expect(await screen.findByText("The workspace is ready, with no events yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit Opportunity" })).toBeInTheDocument();
  });

  it("prompts for authentication when a guest selects a protected action", async () => {
    stubFetch({
      [HEALTH]: () => jsonResponse(healthBody()),
      [EVENTS]: () => jsonResponse(emptyEvents),
    });

    render(<App initialMode="guest" />);
    expect(await screen.findByText("The workspace is ready, with no events yet")).toBeInTheDocument();

    // Click protected action: Submit Opportunity
    const submitBtn = screen.getByRole("button", { name: "Submit Opportunity" });
    await userEvent.click(submitBtn);

    // Friendly authentication prompt modal should appear
    expect(await screen.findByText("Authentication Required")).toBeInTheDocument();
    expect(screen.getByText(/submit an opportunity URL/i)).toBeInTheDocument();
  });
});
