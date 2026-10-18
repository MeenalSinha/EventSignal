/** Service for Phase 7: Student Needs, Matches, Handovers, Event Memories, and Tasks. */

import type {
  EventMemory,
  EventMemoryCreate,
  FollowUpTask,
  FollowUpTaskCreate,
  HelperMatch,
  LegacyHandover,
  LegacyHandoverCreate,
  MatchStatus,
  NeedStatus,
  Phase7ListResponse,
  StudentNeed,
  StudentNeedCreate,
} from "../types/phase7";
import { requestJson } from "./apiClient";
import { getAuthHeaders } from "./authService";

function makeHeaders(institutionId: string): Record<string, string> {
  return {
    ...getAuthHeaders(),
    "X-Institution-Id": institutionId,
  };
}

// ---------------------------------------------------------------------------
// Student Needs
// ---------------------------------------------------------------------------

export async function createStudentNeed(
  institutionId: string,
  data: StudentNeedCreate
): Promise<StudentNeed> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/needs`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: data,
    }
  );
  return response.body as StudentNeed;
}

export async function fetchMyStudentNeeds(
  institutionId: string
): Promise<Phase7ListResponse<StudentNeed>> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/needs`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  return response.body as Phase7ListResponse<StudentNeed>;
}

export async function runMatchingForNeed(
  institutionId: string,
  needId: string
): Promise<HelperMatch[]> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/needs/${encodeURIComponent(needId)}/run-matching`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
    }
  );
  const data = response.body as { items?: HelperMatch[] } | HelperMatch[];
  return Array.isArray(data) ? data : (data?.items ?? []);
}

export async function fetchMatchesForNeed(
  institutionId: string,
  needId: string
): Promise<HelperMatch[]> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/needs/${encodeURIComponent(needId)}/matches`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  const data = response.body as { items?: HelperMatch[] } | HelperMatch[];
  return Array.isArray(data) ? data : (data?.items ?? []);
}

export async function updateMatchStatus(
  institutionId: string,
  matchId: string,
  status: MatchStatus
): Promise<HelperMatch> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/matches/${encodeURIComponent(matchId)}/status`,
    {
      method: "PATCH",
      headers: makeHeaders(institutionId),
      body: { status },
    }
  );
  return response.body as HelperMatch;
}

export async function updateNeedStatus(
  institutionId: string,
  needId: string,
  status: NeedStatus
): Promise<StudentNeed> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/needs/${encodeURIComponent(needId)}`,
    {
      method: "PATCH",
      headers: makeHeaders(institutionId),
      body: { status },
    }
  );
  return response.body as StudentNeed;
}

// ---------------------------------------------------------------------------
// Legacy Handovers
// ---------------------------------------------------------------------------

export async function createHandover(
  institutionId: string,
  data: LegacyHandoverCreate
): Promise<LegacyHandover> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/handovers`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: data,
    }
  );
  return response.body as LegacyHandover;
}

export async function fetchHandovers(
  institutionId: string,
  params?: { position_id?: string; status?: string }
): Promise<Phase7ListResponse<LegacyHandover>> {
  const query = new URLSearchParams();
  if (params?.position_id) query.set("position_id", params.position_id);
  if (params?.status) query.set("status", params.status);
  const qStr = query.toString() ? `?${query.toString()}` : "";

  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/handovers${qStr}`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  return response.body as Phase7ListResponse<LegacyHandover>;
}

export async function submitHandover(
  institutionId: string,
  handoverId: string
): Promise<LegacyHandover> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/handovers/${encodeURIComponent(handoverId)}/submit`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
    }
  );
  return response.body as LegacyHandover;
}

export async function acknowledgeHandover(
  institutionId: string,
  handoverId: string
): Promise<LegacyHandover> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/handovers/${encodeURIComponent(handoverId)}/acknowledge`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
    }
  );
  return response.body as LegacyHandover;
}

// ---------------------------------------------------------------------------
// Event Memories
// ---------------------------------------------------------------------------

export async function createEventMemory(
  institutionId: string,
  data: EventMemoryCreate
): Promise<EventMemory> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/memories`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: data,
    }
  );
  return response.body as EventMemory;
}

export async function fetchEventMemories(
  institutionId: string,
  params?: { is_current?: boolean; opportunity_id?: string }
): Promise<Phase7ListResponse<EventMemory>> {
  const query = new URLSearchParams();
  if (params?.is_current !== undefined) query.set("is_current", String(params.is_current));
  if (params?.opportunity_id) query.set("opportunity_id", params.opportunity_id);
  const qStr = query.toString() ? `?${query.toString()}` : "";

  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/memories${qStr}`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  return response.body as Phase7ListResponse<EventMemory>;
}

// ---------------------------------------------------------------------------
// Follow-Up Tasks
// ---------------------------------------------------------------------------

export async function createFollowUpTask(
  institutionId: string,
  data: FollowUpTaskCreate
): Promise<FollowUpTask> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/tasks`,
    {
      method: "POST",
      headers: makeHeaders(institutionId),
      body: data,
    }
  );
  return response.body as FollowUpTask;
}

export async function fetchMyFollowUpTasks(
  institutionId: string,
  params?: { is_completed?: boolean }
): Promise<Phase7ListResponse<FollowUpTask>> {
  const query = new URLSearchParams();
  if (params?.is_completed !== undefined) query.set("is_completed", String(params.is_completed));
  const qStr = query.toString() ? `?${query.toString()}` : "";

  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/tasks${qStr}`,
    {
      headers: makeHeaders(institutionId),
    }
  );
  return response.body as Phase7ListResponse<FollowUpTask>;
}

export async function completeFollowUpTask(
  institutionId: string,
  taskId: string
): Promise<FollowUpTask> {
  const response = await requestJson(
    `/api/v1/institutions/${encodeURIComponent(institutionId)}/tasks/${encodeURIComponent(taskId)}`,
    {
      method: "PATCH",
      headers: makeHeaders(institutionId),
      body: { is_completed: true },
    }
  );
  return response.body as FollowUpTask;
}
