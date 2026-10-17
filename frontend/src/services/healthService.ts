import type { ComponentHealth, ComponentStatus, HealthResponse, HealthStatus } from "../types/health";
import { requestJson } from "./apiClient";
import { invalid, isObject } from "./validation";

export const HEALTH_PATH = "/api/v1/health";

const HEALTH_STATUSES: readonly string[] = ["healthy", "degraded", "unhealthy"] satisfies HealthStatus[];
const COMPONENT_STATUSES: readonly string[] = ["ok", "degraded", "unavailable"] satisfies ComponentStatus[];

function parseComponent(value: unknown): ComponentHealth {
  if (!isObject(value) || typeof value.message !== "string" || typeof value.status !== "string") {
    throw invalid("health component");
  }
  if (!COMPONENT_STATUSES.includes(value.status)) throw invalid("health component status");
  return { status: value.status as ComponentStatus, message: value.message };
}

/** Validates an untrusted payload instead of trusting a type assertion. */
export function parseHealthResponse(body: unknown): HealthResponse {
  if (!isObject(body)) throw invalid("health response");
  const { status, message, app_name, version, environment, checked_at, components } = body;

  if (typeof status !== "string" || !HEALTH_STATUSES.includes(status)) throw invalid("health status");
  if (
    typeof message !== "string" ||
    typeof app_name !== "string" ||
    typeof version !== "string" ||
    typeof environment !== "string" ||
    typeof checked_at !== "string"
  ) {
    throw invalid("health response");
  }
  if (!isObject(components)) throw invalid("health components");

  return {
    status: status as HealthStatus,
    message,
    app_name,
    version,
    environment,
    checked_at,
    components: Object.fromEntries(Object.entries(components).map(([name, c]) => [name, parseComponent(c)])),
  };
}

/** A 503 carries a valid health body describing the problem, so it is returned, not thrown. */
export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const { body } = await requestJson(HEALTH_PATH, {
    acceptStatuses: [503],
    ...(signal ? { signal } : {}),
  });
  return parseHealthResponse(body);
}
