import { describe, expect, it } from "vitest";
import { healthBody, jsonResponse, stubFetch } from "../test/helpers";
import { ApiError } from "./apiClient";
import { fetchEvents } from "./eventsService";
import { HEALTH_PATH, fetchHealth, parseHealthResponse } from "./healthService";

async function failureOf(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError);
    return error as ApiError;
  }
  throw new Error("expected the request to fail");
}

describe("fetchHealth", () => {
  it("calls the configured base URL and returns the parsed body", async () => {
    const fetchMock = stubFetch({ [HEALTH_PATH]: () => jsonResponse(healthBody()) });
    const health = await fetchHealth();
    expect(fetchMock.mock.calls[0]?.[0]).toBe(`http://api.test${HEALTH_PATH}`);
    expect(health.status).toBe("healthy");
    expect(health.components.database?.status).toBe("ok");
  });

  it("returns the documented body of a 503 instead of treating it as a connection failure", async () => {
    const body = healthBody({
      status: "unhealthy",
      components: { api: { status: "ok", message: "x" }, database: { status: "unavailable", message: "down" } },
    });
    stubFetch({ [HEALTH_PATH]: () => jsonResponse(body, 503) });
    expect((await fetchHealth()).status).toBe("unhealthy");
  });

  it("reports an unreachable backend as a network error", async () => {
    stubFetch({});
    expect((await failureOf(fetchHealth())).kind).toBe("network");
  });

  it("reports other HTTP errors", async () => {
    stubFetch({ [HEALTH_PATH]: () => jsonResponse({ error: "x" }, 500) });
    const error = await failureOf(fetchHealth());
    expect(error.kind).toBe("http");
    expect(error.status).toBe(500);
  });

  it("reports a timeout distinctly", async () => {
    stubFetch({
      [HEALTH_PATH]: () => {
        throw new DOMException("timed out", "TimeoutError");
      },
    });
    expect((await failureOf(fetchHealth())).kind).toBe("timeout");
  });

  it("rejects non-JSON bodies", async () => {
    stubFetch({ [HEALTH_PATH]: () => new Response("<html>proxy error</html>", { status: 200 }) });
    expect((await failureOf(fetchHealth())).kind).toBe("invalid-response");
  });

  it("does not report cancellation as a failure", async () => {
    stubFetch({ [HEALTH_PATH]: () => new Promise<Response>(() => undefined) });
    const controller = new AbortController();
    const pending = fetchHealth(controller.signal);
    controller.abort();
    await expect(pending).rejects.not.toBeInstanceOf(ApiError);
  });
});

describe("parseHealthResponse", () => {
  it.each([
    ["null", null],
    ["a string", "ok"],
    ["an unknown status", healthBody({ status: "great" })],
    ["a missing version", healthBody({ version: undefined })],
    ["bad components", healthBody({ components: [] })],
    ["a bad component status", healthBody({ components: { api: { status: "fine", message: "x" } } })],
  ])("rejects %s", (_name, payload) => {
    expect(() => parseHealthResponse(payload)).toThrow(ApiError);
  });
});

describe("fetchEvents", () => {
  it("rejects malformed payloads instead of trusting them", async () => {
    stubFetch({ "/api/v1/events": () => jsonResponse({ items: [{ id: 5 }], total: 1, limit: 1, offset: 0 }) });
    expect((await failureOf(fetchEvents())).kind).toBe("invalid-response");
  });
});
