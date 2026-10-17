/** Service for Phase 4 opportunity assessment API. */

import type { OpportunityAssessment } from "../types/assessment";
import { requestJson } from "./apiClient";
import { isObject } from "./validation";

export const ASSESS_PATH = (id: string) => `/api/v1/opportunities/${id}/assess`;
export const GET_ASSESSMENT_PATH = (id: string) => `/api/v1/opportunities/${id}/assessment`;

function parseAssessment(val: unknown): OpportunityAssessment {
  if (!isObject(val) || typeof val.id !== "string" || typeof val.opportunity_id !== "string") {
    throw new Error("Invalid assessment response");
  }
  return {
    id: String(val.id),
    opportunity_id: String(val.opportunity_id),
    overall_score: Number(val.overall_score ?? 0),
    completeness_score: Number(val.completeness_score ?? 0),
    evidence_quality_score: Number(val.evidence_quality_score ?? 0),
    consistency_score: Number(val.consistency_score ?? 0),
    completeness_explanation: String(val.completeness_explanation ?? ""),
    evidence_quality_explanation: String(val.evidence_quality_explanation ?? ""),
    consistency_explanation: String(val.consistency_explanation ?? ""),
    missing_critical_fields: Array.isArray(val.missing_critical_fields)
      ? (val.missing_critical_fields as string[])
      : [],
    missing_optional_fields: Array.isArray(val.missing_optional_fields)
      ? (val.missing_optional_fields as string[])
      : [],
    ambiguous_fields: Array.isArray(val.ambiguous_fields) ? (val.ambiguous_fields as string[]) : [],
    conflicting_fields: Array.isArray(val.conflicting_fields)
      ? (val.conflicting_fields as string[])
      : [],
    limitations: String(val.limitations ?? ""),
    total_fields_assessed: Number(val.total_fields_assessed ?? 0),
    fields_found_count: Number(val.fields_found_count ?? 0),
    fields_not_found_count: Number(val.fields_not_found_count ?? 0),
    fields_failed_count: Number(val.fields_failed_count ?? 0),
  };
}

/** Trigger (or re-trigger) assessment for an opportunity. */
export async function runAssessment(opportunityId: string): Promise<OpportunityAssessment> {
  const { body } = await requestJson(ASSESS_PATH(opportunityId), {
    method: "POST",
  });
  return parseAssessment(body);
}

/** Fetch the latest persisted assessment (throws if none exists). */
export async function getAssessment(opportunityId: string): Promise<OpportunityAssessment> {
  const { body } = await requestJson(GET_ASSESSMENT_PATH(opportunityId));
  return parseAssessment(body);
}
