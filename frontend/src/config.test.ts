import { describe, expect, it } from "vitest";
import { ConfigurationError, readConfig } from "./config";

const env = (values: Record<string, string | undefined>) => values as unknown as ImportMetaEnv;

describe("readConfig", () => {
  it("rejects a missing API base URL with a helpful message", () => {
    expect(() => readConfig(env({}))).toThrow(ConfigurationError);
    expect(() => readConfig(env({}))).toThrow(/VITE_API_BASE_URL/);
  });

  it("accepts an empty base URL as proxy mode", () => {
    expect(readConfig(env({ VITE_API_BASE_URL: "" })).apiBaseUrl).toBe("");
  });

  it("normalises trailing slashes", () => {
    expect(readConfig(env({ VITE_API_BASE_URL: "http://x.test:8000//" })).apiBaseUrl).toBe("http://x.test:8000");
  });

  it("rejects non-http URLs", () => {
    expect(() => readConfig(env({ VITE_API_BASE_URL: "javascript:alert(1)" }))).toThrow(ConfigurationError);
    expect(() => readConfig(env({ VITE_API_BASE_URL: "not a url" }))).toThrow(ConfigurationError);
  });

  it("validates the timeout", () => {
    expect(readConfig(env({ VITE_API_BASE_URL: "", VITE_REQUEST_TIMEOUT_MS: "1500" })).requestTimeoutMs).toBe(1500);
    expect(readConfig(env({ VITE_API_BASE_URL: "" })).requestTimeoutMs).toBeGreaterThan(0);
    expect(() => readConfig(env({ VITE_API_BASE_URL: "", VITE_REQUEST_TIMEOUT_MS: "-5" }))).toThrow(ConfigurationError);
    expect(() => readConfig(env({ VITE_API_BASE_URL: "", VITE_REQUEST_TIMEOUT_MS: "abc" }))).toThrow(ConfigurationError);
  });
});
