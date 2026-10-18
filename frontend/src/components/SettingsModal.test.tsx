import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SettingsModal, loadUserPreferences } from "./SettingsModal";
import type { UserProfile } from "../types/auth";
import * as authService from "../services/authService";

vi.mock("../services/authService", async () => {
  const actual = await vi.importActual<typeof import("../services/authService")>("../services/authService");
  return {
    ...actual,
    fetchDemoStatus: vi.fn().mockResolvedValue({ demo_mode_enabled: true, demo_dataset_seeded: true }),
    resetDemoEnvironment: vi.fn().mockResolvedValue({ status: "success", message: "Demo reset complete" }),
    seedDemoEnvironment: vi.fn().mockResolvedValue({ status: "success", message: "Demo seed complete" }),
  };
});

const mockStudentUser: UserProfile = {
  user: {
    id: "usr_123",
    email: "student@apex.edu",
    full_name: "Alex Vance",
    is_active: true,
    is_superuser: false,
    created_at: "2026-01-01T00:00:00Z",
  },
  memberships: [
    {
      id: "mem_123",
      institution_id: "inst_apex",
      institution_name: "Apex Institute of Technology",
      institution_slug: "apex-institute",
      role: "student",
      status: "active",
      joined_at: "2024-01-01T00:00:00Z",
    },
  ],
  is_demo: true,
};

describe("SettingsModal", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("does not render when isOpen is false", () => {
    render(
      <SettingsModal
        isOpen={false}
        onClose={vi.fn()}
        currentUser={mockStudentUser}
        onOpenProfile={vi.fn()}
        onLogout={vi.fn()}
        onOpenAuth={vi.fn()}
      />
    );

    expect(screen.queryByText("Settings & Preferences")).not.toBeInTheDocument();
  });

  it("renders modal with user details and switches tabs", async () => {
    const onClose = vi.fn();
    const onOpenProfile = vi.fn();
    const onLogout = vi.fn();

    render(
      <SettingsModal
        isOpen={true}
        onClose={onClose}
        currentUser={mockStudentUser}
        onOpenProfile={onOpenProfile}
        onLogout={onLogout}
        onOpenAuth={vi.fn()}
      />
    );

    expect(screen.getByText("Settings & Preferences")).toBeInTheDocument();
    expect(screen.getByText("Alex Vance")).toBeInTheDocument();
    expect(screen.getByText("student@apex.edu")).toBeInTheDocument();

    // Switch to Display & Feed tab
    fireEvent.click(screen.getByRole("button", { name: "Display & Feed" }));
    expect(screen.getByText("Default Feed Category")).toBeInTheDocument();
    expect(screen.getByText("Feed Card Density")).toBeInTheDocument();

    // Switch to Privacy & Alerts tab
    fireEvent.click(screen.getByRole("button", { name: "Privacy & Alerts" }));
    expect(screen.getByText("Campus Member Discovery")).toBeInTheDocument();
    expect(screen.getByText("Zero Surveillance Guarantee:")).toBeInTheDocument();

    // Switch to Demo & Environment tab
    fireEvent.click(screen.getByRole("button", { name: "Demo & Environment" }));
    expect(screen.getByText("Demo Mode Status")).toBeInTheDocument();
    expect(screen.getByText("Reset Demo Environment")).toBeInTheDocument();

    // Close modal via Done button
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("persists feed preference changes to localStorage", () => {
    render(
      <SettingsModal
        isOpen={true}
        onClose={vi.fn()}
        currentUser={mockStudentUser}
        onOpenProfile={vi.fn()}
        onLogout={vi.fn()}
        onOpenAuth={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Display & Feed" }));
    const select = screen.getByLabelText("Default Feed Category");
    fireEvent.change(select, { target: { value: "hackathon" } });

    const prefs = loadUserPreferences();
    expect(prefs.defaultFeedCategory).toBe("hackathon");
  });

  it("triggers reset demo environment and seeds demo environment", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(
      <SettingsModal
        isOpen={true}
        onClose={vi.fn()}
        currentUser={mockStudentUser}
        onOpenProfile={vi.fn()}
        onLogout={vi.fn()}
        onOpenAuth={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Demo & Environment" }));
    const resetBtn = screen.getByRole("button", { name: "Reset Demo Environment" });
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(authService.resetDemoEnvironment).toHaveBeenCalled();
      expect(screen.getByText("Demo reset complete")).toBeInTheDocument();
    });

    const seedBtn = screen.getByRole("button", { name: "Re-verify Demo Data" });
    fireEvent.click(seedBtn);

    await waitFor(() => {
      expect(authService.seedDemoEnvironment).toHaveBeenCalled();
      expect(screen.getByText("Demo seed complete")).toBeInTheDocument();
    });
  });

  it("renders guest state with sign in button when currentUser is null", () => {
    const onOpenAuth = vi.fn();
    const onClose = vi.fn();

    render(
      <SettingsModal
        isOpen={true}
        onClose={onClose}
        currentUser={null}
        onOpenProfile={vi.fn()}
        onLogout={vi.fn()}
        onOpenAuth={onOpenAuth}
      />
    );

    expect(screen.getByText("Guest Visitor")).toBeInTheDocument();
    const signInBtn = screen.getByRole("button", { name: "Sign In or Register" });
    fireEvent.click(signInBtn);

    expect(onClose).toHaveBeenCalled();
    expect(onOpenAuth).toHaveBeenCalled();
  });
});
