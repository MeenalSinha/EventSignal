/** Phase 4: Opportunity assessment types. */

export interface SourceClaim {
  value: string;
  supporting_excerpt: string | null;
}

export interface ConflictDetail {
  field_name: string;
  sources_count: number;
  competing_values: Record<string, SourceClaim>;
  explanation: string;
}

export interface OpportunityAssessment {
  id: string;
  opportunity_id: string;
  policy_version: string;
  overall_score: number;
  completeness_score: number;
  evidence_quality_score: number;
  consistency_score: number;
  completeness_explanation: string;
  evidence_quality_explanation: string;
  consistency_explanation: string;
  missing_critical_fields: string[];
  missing_optional_fields: string[];
  ambiguous_fields: string[];
  conflicting_fields: string[];
  conflict_details: ConflictDetail[];
  limitations: string;
  total_fields_assessed: number;
  fields_found_count: number;
  fields_not_found_count: number;
  fields_failed_count: number;
}
