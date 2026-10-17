/** Frontend runtime configuration, read once from Vite environment variables. */

export class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigurationError";
  }
}

export interface AppConfig {
  /** Backend base URL without a trailing slash. Empty string means same-origin. */
  apiBaseUrl: string;
  requestTimeoutMs: number;
}

const DEFAULT_REQUEST_TIMEOUT_MS = 8000;

export function readConfig(env: ImportMetaEnv): AppConfig {
  const rawBase = env.VITE_API_BASE_URL;
  if (rawBase === undefined) {
    throw new ConfigurationError(
      "VITE_API_BASE_URL is not set. Copy .env.example to .env in the repository root and restart the dev server.",
    );
  }

  const apiBaseUrl = rawBase.trim().replace(/\/+$/, "");
  if (apiBaseUrl !== "") {
    try {
      const parsed = new URL(apiBaseUrl);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") throw new Error("protocol");
    } catch {
      throw new ConfigurationError("VITE_API_BASE_URL must be an http(s) URL, or empty for proxy mode.");
    }
  }

  const rawTimeout = env.VITE_REQUEST_TIMEOUT_MS;
  let requestTimeoutMs = DEFAULT_REQUEST_TIMEOUT_MS;
  if (rawTimeout !== undefined && rawTimeout.trim() !== "") {
    const parsed = Number(rawTimeout);
    if (!Number.isInteger(parsed) || parsed <= 0) {
      throw new ConfigurationError("VITE_REQUEST_TIMEOUT_MS must be a positive integer.");
    }
    requestTimeoutMs = parsed;
  }

  return { apiBaseUrl, requestTimeoutMs };
}

let cached: AppConfig | undefined;

/** Lazily reads configuration so a misconfiguration is reported in the UI, not as a blank page. */
export function getConfig(): AppConfig {
  cached ??= readConfig(import.meta.env);
  return cached;
}
