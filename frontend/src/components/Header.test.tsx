import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Header } from "./Header";
import type { Opportunity } from "../types/opportunity";

const mockOpportunities: Opportunity[] = [
  {
    id: "op-1",
    title: "Apex Hackathon 2026",
    event_name: "Apex Hackathon 2026",
    opportunity_type: "hackathon",
    organizer: "Apex CS Society",
    start_date: "2026-11-01T00:00:00Z",
    end_date: "2026-11-03T00:00:00Z",
    registration_deadline: "2026-10-25T00:00:00Z",
    submission_deadline: "2026-11-03T00:00:00Z",
    location: "Campus Hall A",
    mode: "offline",
    eligibility: "All students",
    skills_required: "Python, React",
    compensation: "$5,000 Prizes",
    application_url: "https://hack.apex.edu",
    sources: [],
    evidence: [],
    created_at: "2026-10-01T00:00:00Z",
    updated_at: "2026-10-01T00:00:00Z",
  },
  {
    id: "op-2",
    title: "Robotics Workshop",
    event_name: "Robotics Workshop",
    opportunity_type: "workshop",
    organizer: "Engineering Dept",
    start_date: "2026-11-10T00:00:00Z",
    end_date: "2026-11-10T00:00:00Z",
    registration_deadline: "2026-11-05T00:00:00Z",
    submission_deadline: null,
    location: "Lab 3",
    mode: "offline",
    eligibility: "Engineers",
    skills_required: "C++, ROS",
    compensation: "Free",
    application_url: "https://robotics.apex.edu",
    sources: [],
    evidence: [],
    created_at: "2026-10-02T00:00:00Z",
    updated_at: "2026-10-02T00:00:00Z",
  },
];

import type { HealthResponse } from "../types/health";
import type { ResourceState } from "../hooks/useRemoteResource";

const mockHealthState: ResourceState<HealthResponse> = {
  status: "success",
  data: {
    status: "healthy",
    message: "Service running normally",
    app_name: "eventsignal-backend",
    version: "0.1.0",
    environment: "demo",
    checked_at: "2026-10-18T00:00:00Z",
    components: {
      database: { status: "ok", message: "connected" },
    },
  },
};

describe("Header Search Bar", () => {
  it("renders search bar input with accessible attributes", () => {
    render(
      <Header
        health={mockHealthState}
        searchQuery=""
        onSearchChange={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText("Search opportunities, people, events, colleges...");
    expect(input).toBeInTheDocument();
  });

  it("updates query when typing and shows clear button", () => {
    const onSearchChange = vi.fn();
    const { rerender } = render(
      <Header
        health={mockHealthState}
        searchQuery=""
        onSearchChange={onSearchChange}
      />
    );

    const input = screen.getByPlaceholderText("Search opportunities, people, events, colleges...");
    fireEvent.change(input, { target: { value: "hackathon" } });
    expect(onSearchChange).toHaveBeenCalledWith("hackathon");

    // Rerender with active query
    rerender(
      <Header
        health={mockHealthState}
        searchQuery="hackathon"
        onSearchChange={onSearchChange}
      />
    );

    const clearBtn = screen.getByLabelText("Clear search query");
    expect(clearBtn).toBeInTheDocument();
    fireEvent.click(clearBtn);
    expect(onSearchChange).toHaveBeenCalledWith("");
  });

  it("shows instant matching opportunities and section jumps when focused with query", () => {
    const onSelectOpportunity = vi.fn();
    const onViewChange = vi.fn();

    render(
      <Header
        health={mockHealthState}
        searchQuery="hackathon"
        opportunities={mockOpportunities}
        onSelectOpportunity={onSelectOpportunity}
        onViewChange={onViewChange}
      />
    );

    const input = screen.getByPlaceholderText("Search opportunities, people, events, colleges...");
    fireEvent.focus(input);

    expect(screen.getByText("Apex Hackathon 2026")).toBeInTheDocument();
    expect(screen.getByText("Matching Opportunities (1)")).toBeInTheDocument();

    // Click matching opportunity
    fireEvent.click(screen.getByText("Apex Hackathon 2026"));
    expect(onSelectOpportunity).toHaveBeenCalledWith(mockOpportunities[0]);
    expect(onViewChange).toHaveBeenCalledWith("home");
  });

  it("submits search form and calls onSearchSubmit", () => {
    const onSearchSubmit = vi.fn();

    render(
      <Header
        health={mockHealthState}
        searchQuery="robotics"
        onSearchSubmit={onSearchSubmit}
      />
    );

    const form = screen.getByRole("search");
    fireEvent.submit(form);
    expect(onSearchSubmit).toHaveBeenCalledWith("robotics");
  });

  it("does not render notification badge when count is 0 or undefined", () => {
    const { container, rerender } = render(
      <Header
        health={mockHealthState}
        notificationsCount={0}
      />
    );
    expect(container.querySelector(".bg-alert")).toBeNull();

    rerender(
      <Header
        health={mockHealthState}
      />
    );
    expect(container.querySelector(".bg-alert")).toBeNull();
  });

  it("renders notification badge with actual count when count > 0", () => {
    const { container } = render(
      <Header
        health={mockHealthState}
        notificationsCount={5}
      />
    );
    const badge = container.querySelector(".bg-alert");
    expect(badge).not.toBeNull();
    expect(badge).toHaveTextContent("5");
  });
});

