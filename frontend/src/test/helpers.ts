/** Test-only helpers. Synthetic payloads here never ship in the application bundle. */
import { vi } from "vitest";

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export function healthBody(overrides: Record<string, unknown> = {}) {
  return {
    status: "healthy",
    message: "All checks passed.",
    app_name: "EventSignal",
    version: "9.8.7-test",
    environment: "test",
    checked_at: "2030-01-01T10:00:00Z",
    components: {
      api: { status: "ok", message: "API responding." },
      database: { status: "ok", message: "Database reachable and schema present." },
    },
    ...overrides,
  };
}

export const emptyEvents = { items: [], total: 0, limit: 50, offset: 0 };

type Handler = () => Response | Promise<Response>;

/** Replaces fetch with a router keyed by URL path. Unrouted paths fail like an unreachable server. */
export function stubFetch(routes: Record<string, Handler>) {
  const mock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const path = new URL(String(input)).pathname;
    const handler = routes[path];
    // Like real fetch, reject when the request is aborted.
    return new Promise<Response>((resolve, reject) => {
      const signal = init?.signal;
      if (signal?.aborted) return reject(signal.reason);
      signal?.addEventListener("abort", () => reject(signal.reason), { once: true });
      if (!handler) return reject(new TypeError("Failed to fetch"));
      Promise.resolve()
        .then(handler)
        .then(resolve, reject);
    });
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

export const networkDown: Handler = () => {
  throw new TypeError("Failed to fetch");
};
