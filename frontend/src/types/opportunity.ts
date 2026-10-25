import type { MediaAsset } from "./media";

export type OpportunityType =
  | "hackathon"
  | "workshop"
  | "conference"
  | "competition"
  | "internship"
  | "fellowship"
  | "research"
  | "mentorship"
  | "other";

export type ParticipationMode = "online" | "offline" | "hybrid";

export type EvidenceStatus =
  | "found"
  | "multi_source"
  | "needs_verification"
  | "not_found"
  | "sources_disagree"
  | "extraction_failed"
  | "not_assessed";

export type ExtractionMethod = "manual" | "rule_based" | "llm" | "structured";

export interface SourceReference {
  id: string;
  opportunity_id: string;
  source_type: string;
  url: string | null;
  title: string | null;
  retrieved_at: string | null;
  content_hash: string | null;
  source_metadata: Record<string, unknown> | null;
}

export interface FieldEvidence {
  id: string;
  opportunity_id: string;
  source_id: string | null;
  field_name: string;
  extracted_value: string | null;
  supporting_excerpt: string | null;
  extraction_method: ExtractionMethod;
  evidence_status: EvidenceStatus;
}

export interface Opportunity {
  id: string;
  title: string | null;
  event_name?: string | null;
  opportunity_type: OpportunityType | null;
  organizer: string | null;
  start_date: string | null;
  end_date: string | null;
  registration_deadline: string | null;
  submission_deadline: string | null;
  location: string | null;
  mode: ParticipationMode | null;
  eligibility: string | null;
  skills_required: string | null;
  compensation: string | null;
  application_url: string | null;
  poster_url?: string | null | undefined;
  media_assets?: MediaAsset[] | undefined;
  sources: SourceReference[];
  evidence: FieldEvidence[];
  created_at: string;
  updated_at: string;
}

export interface OpportunityIngestRequest {
  url: string;
  force_refresh?: boolean;
}

export interface OpportunityIngestResponse {
  opportunity: Opportunity;
  source_reference: SourceReference;
  is_duplicate: boolean;
  fields_extracted_count: number;
  evidence: FieldEvidence[];
  message: string;
}
