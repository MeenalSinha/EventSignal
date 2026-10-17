/** API client service for institutions, workspaces, units, positions, and RBAC. */

import type {
  CampusAssignment,
  CampusPosition,
  Institution,
  Membership,
  OrganizationalUnit,
  WorkspaceSummary,
} from "../types/institution";
import { getAuthHeaders } from "./authService";
import { ApiError, requestJson } from "./apiClient";

export async function fetchInstitutions(): Promise<Institution[]> {
  try {
    const response = await requestJson("/api/v1/institutions");
    return response.body as Institution[];
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to load institutions: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchInstitution(idOrSlug: string): Promise<Institution> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(idOrSlug)}`);
    return response.body as Institution;
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Institution not found: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchWorkspaceSummary(institutionId: string): Promise<WorkspaceSummary> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/workspace`);
    return response.body as WorkspaceSummary;
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to load workspace summary: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchWorkspaceMembers(institutionId: string): Promise<Membership[]> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/members`, {
      headers: getAuthHeaders(),
    });
    return response.body as Membership[];
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to load workspace members: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchWorkspaceUnits(institutionId: string): Promise<OrganizationalUnit[]> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/units`);
    return response.body as OrganizationalUnit[];
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to load organizational units: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchWorkspacePositions(institutionId: string): Promise<CampusPosition[]> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/positions`);
    return response.body as CampusPosition[];
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to load campus positions: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchWorkspaceAssignments(institutionId: string): Promise<CampusAssignment[]> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/assignments`);
    return response.body as CampusAssignment[];
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to load campus role assignments: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function createInstitution(data: {
  name: string;
  slug: string;
  domain?: string | undefined;
  description?: string | undefined;
  location?: string | undefined;
  contact_email?: string | undefined;
  website_url?: string | undefined;
}): Promise<Institution> {
  try {
    const response = await requestJson("/api/v1/institutions", {
      method: "POST",
      headers: getAuthHeaders(),
      body: data,
    });
    return response.body as Institution;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 409) {
        throw new Error(`Institution slug '${data.slug}' is already taken.`, { cause: error });
      }
      throw new Error(`Failed to create institution: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function joinWorkspace(institutionId: string, role: string): Promise<Membership> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/join`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: { role },
    });
    return response.body as Membership;
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to join workspace: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function createOrganizationalUnit(
  institutionId: string,
  data: {
    name: string;
    code?: string | undefined;
    unit_type?: string | undefined;
    description?: string | undefined;
  }
): Promise<OrganizationalUnit> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/units`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: data,
    });
    return response.body as OrganizationalUnit;
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to create unit: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function createCampusPosition(
  institutionId: string,
  data: {
    title: string;
    unit_id?: string | undefined;
    description?: string | undefined;
    is_leadership?: boolean | undefined;
  }
): Promise<CampusPosition> {
  try {
    const response = await requestJson(`/api/v1/institutions/${encodeURIComponent(institutionId)}/positions`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: data,
    });
    return response.body as CampusPosition;
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to create position: ${error.message}`, { cause: error });
    }
    throw error;
  }
}
