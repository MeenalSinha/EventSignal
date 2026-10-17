/** Authentication and user identity types. */

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface UserMembership {
  id: string;
  institution_id: string;
  institution_name: string | null;
  institution_slug: string | null;
  role: string;
  status: string;
  joined_at: string;
}

export interface UserProfile {
  user: User;
  memberships: UserMembership[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
}
