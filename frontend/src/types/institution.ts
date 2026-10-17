/** Institutional identity, workspaces, units, positions, and RBAC types. */

export type InstitutionStatus = "pending" | "active" | "suspended";
export type InstitutionVerificationStatus = "unverified" | "verified" | "rejected";
export type InstitutionRole =
  | "platform_admin"
  | "institution_admin"
  | "faculty"
  | "student"
  | "alumni"
  | "member";
export type MembershipStatus = "pending" | "active" | "suspended" | "revoked";
export type AssignmentVerificationStatus = "unverified" | "verified" | "rejected";

export interface Institution {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  description: string | null;
  location: string | null;
  contact_email: string | null;
  website_url: string | null;
  status: InstitutionStatus;
  verification_status: InstitutionVerificationStatus;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceSummary {
  institution: Institution;
  total_members: number;
  total_units: number;
  total_positions: number;
  active_assignments: number;
  total_opportunities: number;
}

export interface Membership {
  id: string;
  institution_id: string;
  user_id: string;
  role: InstitutionRole;
  status: MembershipStatus;
  joined_at: string;
  verified_at: string | null;
  verified_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  user_email: string | null;
  user_full_name: string | null;
}

export interface OrganizationalUnit {
  id: string;
  institution_id: string;
  name: string;
  code: string | null;
  unit_type: string;
  parent_id: string | null;
  description: string | null;
  contact_email: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampusPosition {
  id: string;
  institution_id: string;
  unit_id: string | null;
  title: string;
  description: string | null;
  is_leadership: boolean;
  created_at: string;
  updated_at: string;
}

export interface CampusAssignment {
  id: string;
  institution_id: string;
  user_id: string;
  position_id: string;
  unit_id: string | null;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  verification_status: AssignmentVerificationStatus;
  verified_at: string | null;
  verified_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  user_full_name: string | null;
  user_email: string | null;
  position_title: string | null;
  unit_name: string | null;
}

export interface AuditLog {
  id: string;
  institution_id: string | null;
  actor_user_id: string | null;
  action: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}
