import { ApiError } from "./apiClient";

export type JsonObject = Record<string, unknown>;

export function invalid(what: string): ApiError {
  return new ApiError("invalid-response", `The backend returned an unexpected ${what}.`);
}

export function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}
