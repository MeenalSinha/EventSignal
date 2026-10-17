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
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | undefined;
  body?: unknown;
  headers?: Record<string, string> | undefined;
  signal?: AbortSignal | undefined;
  /** Non-2xx statuses whose JSON body is a meaningful, documented response (for example 503 on /health). */
  acceptStatuses?: readonly number[] | undefined;
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

  const method = options.method ?? "GET";
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...options.headers,
  };

  const fetchInit: RequestInit = {
    method,
    headers,
    signal,
  };
  if (options.body !== undefined) {
    fetchInit.body = JSON.stringify(options.body);
  }

  let response: Response;
  try {
    response = await fetch(`${config.apiBaseUrl}${path}`, fetchInit);
  } catch (error) {
    if (options.signal?.aborted) throw error; // caller cancelled; not a failure to report
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new ApiError("timeout", "The backend did not respond in time.");
    }
    throw new ApiError("network", "Could not reach the backend.");
  }

  const accepted = response.ok || (options.acceptStatuses?.includes(response.status) ?? false);
  if (!accepted) {
    let detailMessage = `The backend returned an error (HTTP ${response.status}).`;
    try {
      const errBody = (await response.json()) as { detail?: string; error?: { message?: string } };
      if (typeof errBody.detail === "string") {
        detailMessage = errBody.detail;
      } else if (typeof errBody.error?.message === "string") {
        detailMessage = errBody.error.message;
      }
    } catch {
      // Ignore JSON parse error on error response
    }
    throw new ApiError("http", detailMessage, response.status);
  }

  try {
    return { status: response.status, body: await response.json() };
  } catch {
    throw new ApiError("invalid-response", "The backend returned a response that is not valid JSON.", response.status);
  }
}
