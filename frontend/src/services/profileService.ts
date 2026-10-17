/** Service for student and alumni profile management and member discovery. */

import type { AlumniProfile, MemberDiscovery, StudentProfile } from "../types/profile";
import { ApiError, requestJson } from "./apiClient";
import { getAuthHeaders } from "./authService";

export async function fetchMyStudentProfile(institutionId: string): Promise<StudentProfile | null> {
  try {
    const headers = {
      ...getAuthHeaders(),
      "X-Institution-Id": institutionId,
    };
    const response = await requestJson(`/api/v1/profiles/student/me?institution_id=${encodeURIComponent(institutionId)}`, {
      headers,
      acceptStatuses: [404],
    });
    if (response.status === 404) {
      return null;
    }
    return response.body as StudentProfile;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function saveMyStudentProfile(institutionId: string, data: Partial<StudentProfile>): Promise<StudentProfile> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/profiles/student?institution_id=${encodeURIComponent(institutionId)}`, {
    method: "POST",
    headers,
    body: data,
  });
  return response.body as StudentProfile;
}

export async function fetchMyAlumniProfile(institutionId: string): Promise<AlumniProfile | null> {
  try {
    const headers = {
      ...getAuthHeaders(),
      "X-Institution-Id": institutionId,
    };
    const response = await requestJson(`/api/v1/profiles/alumni/me?institution_id=${encodeURIComponent(institutionId)}`, {
      headers,
      acceptStatuses: [404],
    });
    if (response.status === 404) {
      return null;
    }
    return response.body as AlumniProfile;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function saveMyAlumniProfile(institutionId: string, data: Partial<AlumniProfile>): Promise<AlumniProfile> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const response = await requestJson(`/api/v1/profiles/alumni?institution_id=${encodeURIComponent(institutionId)}`, {
    method: "POST",
    headers,
    body: data,
  });
  return response.body as AlumniProfile;
}

export async function discoverMembers(
  institutionId: string,
  role?: string | undefined,
  query?: string | undefined,
): Promise<MemberDiscovery[]> {
  const headers = {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
  const params = new URLSearchParams({ institution_id: institutionId });
  if (role) params.set("role", role);
  if (query) params.set("q", query);

  const response = await requestJson(`/api/v1/profiles/discovery?${params.toString()}`, {
    headers,
  });
  return response.body as MemberDiscovery[];
}
