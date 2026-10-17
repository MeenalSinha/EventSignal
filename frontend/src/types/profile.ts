/** Profile and member discovery types for Phase 6. */

export type StudentVisibility = "private" | "institution_only" | "public";
export type AlumniVisibility = "private" | "alumni_only" | "students_only" | "public";

export interface StudentProfile {
  id: string;
  user_id: string;
  institution_id: string;
  membership_id: string;
  headline?: string | null;
  bio?: string | null;
  degree_level?: string | null;
  graduation_year?: number | null;
  skills: string[];
  interests: string[];
  career_goals: string[];
  portfolio_url?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  preferred_opportunity_types: string[];
  location_preference?: string | null;
  visibility: StudentVisibility;
  created_at: string;
  updated_at: string;
}

export interface AlumniProfile {
  id: string;
  user_id: string;
  institution_id: string;
  membership_id: string;
  current_title?: string | null;
  current_organization?: string | null;
  professional_domain?: string | null;
  industry?: string | null;
  years_of_experience?: number | null;
  skills: string[];
  mentoring_topics: string[];
  bio?: string | null;
  linkedin_url?: string | null;
  website_url?: string | null;
  willing_to_help: boolean;
  preferred_contact_method?: string | null;
  monthly_request_limit: number;
  active_requests_this_month: number;
  visibility: AlumniVisibility;
  created_at: string;
  updated_at: string;
}

export interface MemberDiscovery {
  user_id: string;
  full_name: string;
  membership_role: string;
  status: string;
  joined_at: string;
  campus_positions: string[];
  student_profile?: StudentProfile | null;
  alumni_profile?: AlumniProfile | null;
  active_help_offers_count: number;
}
