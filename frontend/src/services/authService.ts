/** Authentication service and session management. */

import type { DemoStatusResponse, TokenResponse, UserProfile } from "../types/auth";
import { ApiError, requestJson } from "./apiClient";

const TOKEN_KEY = "eventsignal_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore storage errors in restrictive environments
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore storage errors
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function loginUser(email: string, password: string): Promise<TokenResponse> {
  try {
    const response = await requestJson("/api/v1/auth/login", {
      method: "POST",
      body: { email, password },
    });
    const data = response.body as TokenResponse;
    if (data?.access_token) {
      setStoredToken(data.access_token);
    }
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        throw new Error("Invalid email or password.", { cause: error });
      }
      throw new Error(`Login failed: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function registerUser(email: string, password: string, fullName: string): Promise<TokenResponse> {
  try {
    const response = await requestJson("/api/v1/auth/register", {
      method: "POST",
      body: { email, password, full_name: fullName },
    });
    const data = response.body as TokenResponse;
    if (data?.access_token) {
      setStoredToken(data.access_token);
    }
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 409) {
        throw new Error("An account with this email already exists.", { cause: error });
      }
      throw new Error(`Registration failed: ${error.message}`, { cause: error });
    }
    throw error;
  }
}

export async function fetchCurrentUser(): Promise<UserProfile | null> {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const response = await requestJson("/api/v1/auth/me", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.body as UserProfile;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      clearStoredToken();
      return null;
    }
    throw error;
  }
}

export function logoutUser(): void {
  clearStoredToken();
}

export async function fetchDemoStatus(): Promise<DemoStatusResponse> {
  try {
    const response = await requestJson("/api/v1/auth/demo/status", { method: "GET" });
    return response.body as DemoStatusResponse;
  } catch {
    return { demo_mode_enabled: false, demo_dataset_seeded: false };
  }
}

export async function seedDemoEnvironment(): Promise<{ status: string; message: string }> {
  const token = getStoredToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await requestJson("/api/v1/auth/demo/seed", {
    method: "POST",
    headers,
  });
  return response.body as { status: string; message: string };
}

export async function resetDemoEnvironment(): Promise<{ status: string; message: string }> {
  const token = getStoredToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await requestJson("/api/v1/auth/demo/reset", {
    method: "POST",
    headers,
  });
  return response.body as { status: string; message: string };
}

