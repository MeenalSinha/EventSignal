/** Opportunity list service — wraps GET /api/v1/opportunities.
 *
 * Updated in Phase 4 to return full Opportunity objects (including evidence)
 * so the EventWorkspace can display assessment panels.
 */

import type { Opportunity, FieldEvidence, SourceReference } from "../types/opportunity";
import { requestJson } from "./apiClient";
import { invalid, isNullableString, isObject } from "./validation";

export const OPPORTUNITIES_PATH = "/api/v1/opportunities";
/** Legacy alias — backend still serves this path. */
export const EVENTS_PATH = "/api/v1/events";

export interface OpportunityList {
  items: Opportunity[];
  total: number;
  limit: number;
  offset: number;
}

// Re-export for backwards compatibility with App.tsx useRemoteResource usage
export type { OpportunityList as EventList };

function parseSourceReference(val: unknown): SourceReference {
  if (!isObject(val) || typeof val.id !== "string") throw invalid("source reference");
  return {
    id: String(val.id),
    opportunity_id: String(val.opportunity_id ?? ""),
    source_type: String(val.source_type ?? "other"),
    url: isNullableString(val.url) ? val.url : null,
    title: isNullableString(val.title) ? val.title : null,
    retrieved_at: isNullableString(val.retrieved_at) ? val.retrieved_at : null,
    content_hash: isNullableString(val.content_hash) ? val.content_hash : null,
    source_metadata: isObject(val.source_metadata)
      ? (val.source_metadata as Record<string, unknown>)
      : null,
  };
}

function parseFieldEvidence(val: unknown): FieldEvidence {
  if (!isObject(val) || typeof val.id !== "string") throw invalid("field evidence");
  return {
    id: String(val.id),
    opportunity_id: String(val.opportunity_id ?? ""),
    source_id: isNullableString(val.source_id) ? val.source_id : null,
    field_name: String(val.field_name ?? ""),
    extracted_value: isNullableString(val.extracted_value) ? val.extracted_value : null,
    supporting_excerpt: isNullableString(val.supporting_excerpt) ? val.supporting_excerpt : null,
    extraction_method: String(val.extraction_method ?? "rule_based") as FieldEvidence["extraction_method"],
    evidence_status: String(val.evidence_status ?? "not_assessed") as FieldEvidence["evidence_status"],
  };
}

function parseOpportunity(val: unknown): Opportunity {
  if (!isObject(val) || typeof val.id !== "string") throw invalid("opportunity");
  const title = isNullableString(val.title)
    ? val.title
    : isNullableString(val.event_name)
      ? val.event_name
      : null;
  return {
    id: String(val.id),
    title,
    event_name: title,
    opportunity_type:
      val.opportunity_type != null ? (String(val.opportunity_type) as Opportunity["opportunity_type"]) : null,
    organizer: isNullableString(val.organizer) ? val.organizer : null,
    start_date: isNullableString(val.start_date) ? val.start_date : null,
    end_date: isNullableString(val.end_date) ? val.end_date : null,
    registration_deadline: isNullableString(val.registration_deadline) ? val.registration_deadline : null,
    submission_deadline: isNullableString(val.submission_deadline) ? val.submission_deadline : null,
    location: isNullableString(val.location) ? val.location : null,
    mode: val.mode != null ? (String(val.mode) as Opportunity["mode"]) : null,
    eligibility: isNullableString(val.eligibility) ? val.eligibility : null,
    skills_required: isNullableString(val.skills_required) ? val.skills_required : null,
    compensation: isNullableString(val.compensation) ? val.compensation : null,
    application_url: isNullableString(val.application_url) ? val.application_url : null,
    sources: Array.isArray(val.sources) ? val.sources.map(parseSourceReference) : [],
    evidence: Array.isArray(val.evidence) ? val.evidence.map(parseFieldEvidence) : [],
    created_at: String(val.created_at ?? ""),
    updated_at: String(val.updated_at ?? ""),
  };
}

export function parseOpportunityList(body: unknown): OpportunityList {
  if (
    !isObject(body) ||
    !Array.isArray(body.items) ||
    typeof body.total !== "number" ||
    typeof body.limit !== "number" ||
    typeof body.offset !== "number"
  ) {
    throw invalid("opportunity list");
  }
  return {
    items: body.items.map(parseOpportunity),
    total: body.total,
    limit: body.limit,
    offset: body.offset,
  };
}

/** Fetch the list of all stored opportunities. */
export async function fetchOpportunities(signal?: AbortSignal): Promise<OpportunityList> {
  const { body } = await requestJson(OPPORTUNITIES_PATH, signal ? { signal } : {});
  return parseOpportunityList(body);
}

/** Legacy alias used by App.tsx useRemoteResource hook. Uses EVENTS_PATH for route compatibility. */
export async function fetchEvents(signal?: AbortSignal): Promise<OpportunityList> {
  const { body } = await requestJson(EVENTS_PATH, signal ? { signal } : {});
  return parseOpportunityList(body);
}
