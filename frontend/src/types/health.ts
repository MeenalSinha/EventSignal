export type HealthStatus = "healthy" | "degraded" | "unhealthy";
export type ComponentStatus = "ok" | "degraded" | "unavailable";

export interface ComponentHealth {
  status: ComponentStatus;
  message: string;
}

/** Mirrors backend `HealthResponse` (GET /api/v1/health). */
export interface HealthResponse {
  status: HealthStatus;
  message: string;
  app_name: string;
  version: string;
  environment: string;
  checked_at: string;
  components: Record<string, ComponentHealth>;
}
