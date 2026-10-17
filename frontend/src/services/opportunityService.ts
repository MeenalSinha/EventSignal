/** Service for opportunity intake and evidence retrieval (Phase 3). */

import type {
  FieldEvidence,
  Opportunity,
  OpportunityIngestRequest,
  OpportunityIngestResponse,
  SourceReference,
} from "../types/opportunity";
import { requestJson } from "./apiClient";
import { invalid, isNullableString, isObject } from "./validation";

export const INGEST_PATH = "/api/v1/opportunities/ingest";

function parseSourceReference(val: unknown): SourceReference {
  if (!isObject(val) || typeof val.id !== "string" || typeof val.opportunity_id !== "string") {
    throw invalid("source reference");
  }
  return {
    id: val.id,
    opportunity_id: val.opportunity_id,
    source_type: String(val.source_type ?? "other"),
    url: isNullableString(val.url) ? val.url : null,
    title: isNullableString(val.title) ? val.title : null,
    retrieved_at: isNullableString(val.retrieved_at) ? val.retrieved_at : null,
    content_hash: isNullableString(val.content_hash) ? val.content_hash : null,
    source_metadata: isObject(val.source_metadata) ? (val.source_metadata as Record<string, unknown>) : null,
  };
}

function parseFieldEvidence(val: unknown): FieldEvidence {
  if (
    !isObject(val) ||
    typeof val.id !== "string" ||
    typeof val.opportunity_id !== "string" ||
    typeof val.field_name !== "string"
  ) {
    throw invalid("field evidence");
  }
  return {
    id: val.id,
    opportunity_id: val.opportunity_id,
    source_id: isNullableString(val.source_id) ? val.source_id : null,
    field_name: val.field_name,
    extracted_value: isNullableString(val.extracted_value) ? val.extracted_value : null,
    supporting_excerpt: isNullableString(val.supporting_excerpt) ? val.supporting_excerpt : null,
    extraction_method: (val.extraction_method as FieldEvidence["extraction_method"]) ?? "rule_based",
    evidence_status: (val.evidence_status as FieldEvidence["evidence_status"]) ?? "not_found",
  };
}

function parseOpportunity(val: unknown): Opportunity {
  if (!isObject(val) || typeof val.id !== "string") {
    throw invalid("opportunity");
  }
  const sources = Array.isArray(val.sources) ? val.sources.map(parseSourceReference) : [];
  const evidence = Array.isArray(val.evidence) ? val.evidence.map(parseFieldEvidence) : [];

  return {
    id: val.id,
    title: isNullableString(val.title) ? val.title : null,
    opportunity_type: (val.opportunity_type as Opportunity["opportunity_type"]) ?? null,
    organizer: isNullableString(val.organizer) ? val.organizer : null,
    start_date: isNullableString(val.start_date) ? val.start_date : null,
    end_date: isNullableString(val.end_date) ? val.end_date : null,
    registration_deadline: isNullableString(val.registration_deadline) ? val.registration_deadline : null,
    submission_deadline: isNullableString(val.submission_deadline) ? val.submission_deadline : null,
    location: isNullableString(val.location) ? val.location : null,
    mode: (val.mode as Opportunity["mode"]) ?? null,
    eligibility: isNullableString(val.eligibility) ? val.eligibility : null,
    skills_required: isNullableString(val.skills_required) ? val.skills_required : null,
    compensation: isNullableString(val.compensation) ? val.compensation : null,
    application_url: isNullableString(val.application_url) ? val.application_url : null,
    sources,
    evidence,
    created_at: String(val.created_at ?? ""),
    updated_at: String(val.updated_at ?? ""),
  };
}

export function parseIngestResponse(body: unknown): OpportunityIngestResponse {
  if (!isObject(body) || !isObject(body.opportunity) || !isObject(body.source_reference)) {
    throw invalid("opportunity ingest response");
  }

  const evidence = Array.isArray(body.evidence) ? body.evidence.map(parseFieldEvidence) : [];

  return {
    opportunity: parseOpportunity(body.opportunity),
    source_reference: parseSourceReference(body.source_reference),
    is_duplicate: Boolean(body.is_duplicate),
    fields_extracted_count: typeof body.fields_extracted_count === "number" ? body.fields_extracted_count : 0,
    evidence,
    message: typeof body.message === "string" ? body.message : "Opportunity ingested",
  };
}

export async function ingestOpportunity(
  request: OpportunityIngestRequest,
  signal?: AbortSignal,
): Promise<OpportunityIngestResponse> {
  const { body } = await requestJson(INGEST_PATH, {
    method: "POST",
    body: request,
    signal,
  });
  return parseIngestResponse(body);
}

export const ATTACH_SOURCE_PATH = (id: string) => `/api/v1/opportunities/${id}/sources`;

export async function attachOpportunitySource(
  opportunityId: string,
  request: OpportunityIngestRequest,
  signal?: AbortSignal,
): Promise<OpportunityIngestResponse> {
  const { body } = await requestJson(ATTACH_SOURCE_PATH(opportunityId), {
    method: "POST",
    body: request,
    signal,
  });
  return parseIngestResponse(body);
}

