import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { jsonResponse, stubFetch } from "../test/helpers";
import type { OpportunityAssessment } from "../types/assessment";
import { AssessmentPanel } from "./AssessmentPanel";

const mockAssessment: OpportunityAssessment = {
  id: "asm-100",
  opportunity_id: "opp-test-1",
  overall_score: 0.85,
  completeness_score: 0.9,
  evidence_quality_score: 0.8,
  consistency_score: 1.0,
  completeness_explanation: "9 of 10 fields established from source.",
  evidence_quality_explanation: "Direct structured extraction from primary source.",
  consistency_explanation: "No conflicting source evidence detected.",
  missing_critical_fields: ["registration_deadline"],
  missing_optional_fields: ["submission_deadline"],
  ambiguous_fields: ["skills_required"],
  conflicting_fields: [],
  limitations: "Single source assessment. Verification recommended for critical dates.",
  total_fields_assessed: 10,
  fields_found_count: 8,
  fields_not_found_count: 2,
  fields_failed_count: 0,
};

describe("AssessmentPanel", () => {
  it("renders trigger button and loads evaluation on click", async () => {
    stubFetch({
      "/api/v1/opportunities/opp-test-1/assess": () => jsonResponse(mockAssessment),
    });

    render(<AssessmentPanel opportunityId="opp-test-1" opportunityTitle="Test Hackathon" />);

    const button = screen.getByRole("button", { name: "Evaluate Opportunity" });
    expect(button).toBeInTheDocument();

    await userEvent.click(button);

    // After assessment loads:
    expect(await screen.findByText("85%")).toBeInTheDocument();
    expect(screen.getByText("Evidence Assessment")).toBeInTheDocument();
    expect(screen.getByText(/Test Hackathon/)).toBeInTheDocument();

    // Dimension labels and explanations
    expect(screen.getByText("Completeness")).toBeInTheDocument();
    expect(screen.getByText("9 of 10 fields established from source.")).toBeInTheDocument();
    expect(screen.getByText("Evidence Quality")).toBeInTheDocument();
    expect(screen.getByText("Consistency")).toBeInTheDocument();

    // Counters
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("Fields found")).toBeInTheDocument();

    // Missing fields
    expect(screen.getByText(/Missing critical fields/)).toBeInTheDocument();
    expect(screen.getByText("registration_deadline")).toBeInTheDocument();
    expect(screen.getByText("submission_deadline")).toBeInTheDocument();
    expect(screen.getByText("skills_required")).toBeInTheDocument();

    // Limitations
    expect(screen.getByText("Assessment limitations & caveats")).toBeInTheDocument();
    expect(screen.getByText(/Single source assessment/)).toBeInTheDocument();
  });

  it("handles error during assessment gracefully", async () => {
    stubFetch({
      "/api/v1/opportunities/opp-test-1/assess": () =>
        jsonResponse({ detail: "Opportunity not found" }, 404),
    });

    render(<AssessmentPanel opportunityId="opp-test-1" opportunityTitle="Test Hackathon" />);

    const button = screen.getByRole("button", { name: "Evaluate Opportunity" });
    await userEvent.click(button);

    expect(await screen.findByText("Opportunity not found")).toBeInTheDocument();
    // Button returns to actionable state
    expect(screen.getByRole("button", { name: "Evaluate Opportunity" })).toBeInTheDocument();
  });
});
