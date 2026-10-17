import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { OpportunityIngestResponse } from "../types/opportunity";
import { OpportunityIntakeForm } from "./OpportunityIntakeForm";

const INGEST_PATH = "/api/v1/opportunities/ingest";

const mockSuccessResponse: OpportunityIngestResponse = {
  opportunity: {
    id: "opp-123",
    title: "Global AI Hackathon 2026",
    opportunity_type: "hackathon",
    organizer: "Tech Foundation",
    start_date: "2026-11-01T09:00:00Z",
    end_date: "2026-11-03T18:00:00Z",
    registration_deadline: "2026-10-25T23:59:59Z",
    submission_deadline: null,
    location: "Online / Virtual",
    mode: "online",
    eligibility: "Open to students",
    skills_required: "Python, AI",
    compensation: "$10,000 in prizes",
    application_url: "https://example.com/apply",
    sources: [
      {
        id: "src-1",
        opportunity_id: "opp-123",
        source_type: "opportunity_listing",
        url: "https://example.com/hackathon",
        title: "Global AI Hackathon 2026",
        retrieved_at: "2026-10-17T12:00:00Z",
        content_hash: "abcdef1234567890",
        source_metadata: { status_code: 200 },
      },
    ],
    evidence: [
      {
        id: "ev-1",
        opportunity_id: "opp-123",
        source_id: "src-1",
        field_name: "title",
        extracted_value: "Global AI Hackathon 2026",
        supporting_excerpt: "<title>: Global AI Hackathon 2026",
        extraction_method: "structured",
        evidence_status: "found",
      },
      {
        id: "ev-2",
        opportunity_id: "opp-123",
        source_id: "src-1",
        field_name: "submission_deadline",
        extracted_value: null,
        supporting_excerpt: null,
        extraction_method: "rule_based",
        evidence_status: "not_found",
      },
    ],
    created_at: "2026-10-17T12:00:00Z",
    updated_at: "2026-10-17T12:00:00Z",
  },
  source_reference: {
    id: "src-1",
    opportunity_id: "opp-123",
    source_type: "opportunity_listing",
    url: "https://example.com/hackathon",
    title: "Global AI Hackathon 2026",
    retrieved_at: "2026-10-17T12:00:00Z",
    content_hash: "abcdef1234567890",
    source_metadata: { status_code: 200 },
  },
  is_duplicate: false,
  fields_extracted_count: 1,
  evidence: [
    {
      id: "ev-1",
      opportunity_id: "opp-123",
      source_id: "src-1",
      field_name: "title",
      extracted_value: "Global AI Hackathon 2026",
      supporting_excerpt: "<title>: Global AI Hackathon 2026",
      extraction_method: "structured",
      evidence_status: "found",
    },
    {
      id: "ev-2",
      opportunity_id: "opp-123",
      source_id: "src-1",
      field_name: "submission_deadline",
      extracted_value: null,
      supporting_excerpt: null,
      extraction_method: "rule_based",
      evidence_status: "not_found",
    },
  ],
  message: "Opportunity ingested and evidence recorded successfully.",
};

describe("OpportunityIntakeForm", () => {
  it("renders form elements and submits valid URL", async () => {
    stubFetch({
      [INGEST_PATH]: () => jsonResponse(mockSuccessResponse, 201),
    });

    const onSuccess = vi.fn();
    render(<OpportunityIntakeForm onIngestSuccess={onSuccess} />);

    expect(screen.getByLabelText("Opportunity URL")).toBeInTheDocument();
    const input = screen.getByRole("textbox", { name: "Opportunity URL" });
    const submitBtn = screen.getByRole("button", { name: "Analyze & Ingest Opportunity" });

    await userEvent.type(input, "https://example.com/hackathon");
    await userEvent.click(submitBtn);

    expect(await screen.findByText("Opportunity Ingested Successfully")).toBeInTheDocument();
    expect(screen.getAllByText("Global AI Hackathon 2026").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Tech Foundation")).toBeInTheDocument();
    expect(screen.getByText("Found in source")).toBeInTheDocument();
    expect(screen.getByText("Not found")).toBeInTheDocument();
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("handles duplicate URL responses honestly", async () => {
    const duplicateResponse: OpportunityIngestResponse = {
      ...mockSuccessResponse,
      is_duplicate: true,
      message: "Opportunity already ingested. Returned existing record without re-fetching.",
    };

    stubFetch({
      [INGEST_PATH]: () => jsonResponse(duplicateResponse, 200),
    });

    render(<OpportunityIntakeForm />);
    const input = screen.getByRole("textbox", { name: "Opportunity URL" });
    await userEvent.type(input, "https://example.com/hackathon");
    await userEvent.click(screen.getByRole("button", { name: "Analyze & Ingest Opportunity" }));

    expect(await screen.findByText("Existing Opportunity Returned")).toBeInTheDocument();
    expect(screen.getByText(/Returned existing record without re-fetching/)).toBeInTheDocument();
  });

  it("displays backend SSRF or validation error", async () => {
    stubFetch({
      [INGEST_PATH]: () =>
        jsonResponse(
          {
            detail: "Destination IP address 127.0.0.1 is private, internal, or loopback",
          },
          400,
        ),
    });

    render(<OpportunityIntakeForm />);
    const input = screen.getByRole("textbox", { name: "Opportunity URL" });
    await userEvent.type(input, "http://127.0.0.1/secret");
    await userEvent.click(screen.getByRole("button", { name: "Analyze & Ingest Opportunity" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/private, internal, or loopback/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("can reset form and ingest another opportunity", async () => {
    stubFetch({
      [INGEST_PATH]: () => jsonResponse(mockSuccessResponse, 201),
    });

    render(<OpportunityIntakeForm />);
    await userEvent.type(screen.getByRole("textbox", { name: "Opportunity URL" }), "https://example.com/hackathon");
    await userEvent.click(screen.getByRole("button", { name: "Analyze & Ingest Opportunity" }));

    expect(await screen.findByText("Opportunity Ingested Successfully")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Ingest Another" }));
    await waitFor(() => {
      expect(screen.getByRole("textbox", { name: "Opportunity URL" })).toBeInTheDocument();
    });
  });
});
