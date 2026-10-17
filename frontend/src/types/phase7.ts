/** Phase 7 types: Gap-to-Helper Matching & EventSignal Legacy. */

// ---------------------------------------------------------------------------
// Student Needs
// ---------------------------------------------------------------------------

export type NeedStatus = "open" | "matched" | "resolved" | "withdrawn";
export type NeedUrgency = "low" | "medium" | "high";

export interface StudentNeed {
  id: string;
  student_profile_id: string;
  institution_id: string;
  title: string;
  category: string;
  description: string | null;
  preferred_delivery_mode: string | null;
  urgency: NeedUrgency;
  status: NeedStatus;
  extra_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface StudentNeedCreate {
  title: string;
  category: string;
  description?: string | undefined;
  preferred_delivery_mode?: string | undefined;
  urgency?: NeedUrgency | undefined;
}

// ---------------------------------------------------------------------------
// Helper Matches
// ---------------------------------------------------------------------------

export type MatchStatus = "proposed" | "accepted" | "dismissed" | "expired";

export interface RuleResult {
  rule: string;
  matched: boolean | null;
  weight: number;
  contribution: number;
  evidence: string;
}

export interface HelperMatch {
  id: string;
  need_id: string;
  help_offer_id: string;
  institution_id: string;
  score: number;
  rule_results: RuleResult[];
  summary_explanation: string | null;
  uncertainty_notes: string | null;
  scorer_version: string;
  is_seen: boolean;
  status: MatchStatus;
  created_at: string;
  updated_at: string;
  offer_title: string | null;
  offer_category: string | null;
  offer_delivery_mode: string | null;
  offer_owner_name: string | null;
}

// ---------------------------------------------------------------------------
// Legacy Handovers
// ---------------------------------------------------------------------------

export type HandoverStatus = "draft" | "submitted" | "acknowledged" | "superseded";

export interface LegacyHandover {
  id: string;
  institution_id: string;
  position_id: string | null;
  outgoing_user_id: string;
  incoming_user_id: string | null;
  title: string;
  accomplishments_summary: string | null;
  ongoing_work: string | null;
  key_contacts: Array<{
    name: string;
    role?: string;
    email?: string;
    notes?: string;
  }>;
  lessons_learned: string | null;
  recommended_first_steps: string | null;
  version: number;
  status: HandoverStatus;
  acknowledged_at: string | null;
  created_at: string;
  updated_at: string;
  position_title: string | null;
  outgoing_user_name: string | null;
  incoming_user_name: string | null;
}

export interface LegacyHandoverCreate {
  title: string;
  position_id?: string | undefined;
  incoming_user_id?: string | undefined;
  accomplishments_summary?: string | undefined;
  ongoing_work?: string | undefined;
  key_contacts?: Array<{ name: string; role?: string | undefined; email?: string | undefined; notes?: string | undefined }> | undefined;
  lessons_learned?: string | undefined;
  recommended_first_steps?: string | undefined;
}

// ---------------------------------------------------------------------------
// Event Memories
// ---------------------------------------------------------------------------

export interface EventMemory {
  id: string;
  institution_id: string;
  opportunity_id: string | null;
  handover_id: string | null;
  author_user_id: string;
  title: string;
  what_worked: string | null;
  what_did_not_work: string | null;
  attendance_notes: string | null;
  outcome_summary: string | null;
  context_notes: string | null;
  tags: string[];
  superseded_by_id: string | null;
  is_current: boolean;
  extra_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  author_name: string | null;
  opportunity_title: string | null;
}

export interface EventMemoryCreate {
  title: string;
  opportunity_id?: string | undefined;
  what_worked?: string | undefined;
  what_did_not_work?: string | undefined;
  attendance_notes?: string | undefined;
  outcome_summary?: string | undefined;
  context_notes?: string | undefined;
  tags?: string[] | undefined;
}

// ---------------------------------------------------------------------------
// Follow-Up Tasks
// ---------------------------------------------------------------------------

export type TaskSource = "handover" | "match" | "manual";
export type TaskPriority = "low" | "medium" | "high";

export interface FollowUpTask {
  id: string;
  institution_id: string;
  source: TaskSource;
  handover_id: string | null;
  match_id: string | null;
  title: string;
  description: string | null;
  assignee_user_id: string;
  creator_user_id: string;
  due_date: string | null;
  priority: TaskPriority;
  is_completed: boolean;
  completed_at: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  assignee_name: string | null;
  creator_name: string | null;
}

export interface FollowUpTaskCreate {
  title: string;
  assignee_user_id: string;
  description?: string | undefined;
  handover_id?: string | undefined;
  match_id?: string | undefined;
  due_date?: string | undefined;
  priority?: TaskPriority | undefined;
}

// Paginated list response shape
export interface Phase7ListResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
