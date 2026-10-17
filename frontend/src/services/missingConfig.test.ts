import { afterEach, describe, expect, it, vi } from "vitest";

describe("missing configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("surfaces a configuration ApiError rather than crashing or guessing a URL", async () => {
    vi.resetModules();
    vi.stubEnv("VITE_API_BASE_URL", undefined as unknown as string);
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const { fetchHealth } = await import("./healthService");
    const { ApiError } = await import("./apiClient");

    const error = await fetchHealth().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as InstanceType<typeof ApiError>).kind).toBe("configuration");
    expect((error as Error).message).toMatch(/VITE_API_BASE_URL is not set/);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
