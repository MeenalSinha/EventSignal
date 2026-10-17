/** The single place where the frontend talks HTTP to the backend. */

import { getConfig, ConfigurationError } from "../config";

export type ApiErrorKind = "configuration" | "network" | "timeout" | "http" | "invalid-response";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | undefined;

  constructor(kind: ApiErrorKind, message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

export interface JsonResponse {
  status: number;
  body: unknown;
}

interface RequestOptions {
  signal?: AbortSignal;
  /** Non-2xx statuses whose JSON body is a meaningful, documented response (for example 503 on /health). */
  acceptStatuses?: readonly number[];
}

export async function requestJson(path: string, options: RequestOptions = {}): Promise<JsonResponse> {
  let config;
  try {
    config = getConfig();
  } catch (error) {
    if (error instanceof ConfigurationError) throw new ApiError("configuration", error.message);
    throw error;
  }

  const timeout = AbortSignal.timeout(config.requestTimeoutMs);
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;

  let response: Response;
  try {
    response = await fetch(`${config.apiBaseUrl}${path}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    });
  } catch (error) {
    if (options.signal?.aborted) throw error; // caller cancelled; not a failure to report
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new ApiError("timeout", "The backend did not respond in time.");
    }
    throw new ApiError("network", "Could not reach the backend.");
  }

  const accepted = response.ok || (options.acceptStatuses?.includes(response.status) ?? false);
  if (!accepted) {
    throw new ApiError("http", `The backend returned an error (HTTP ${response.status}).`, response.status);
  }

  try {
    return { status: response.status, body: await response.json() };
  } catch {
    throw new ApiError("invalid-response", "The backend returned a response that is not valid JSON.", response.status);
  }
}
