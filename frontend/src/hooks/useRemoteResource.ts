import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../services/apiClient";

export type ResourceState<T> =
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: ApiError };

function toApiError(error: unknown): ApiError {
  return error instanceof ApiError ? error : new ApiError("network", "An unexpected error occurred.");
}

/**
 * Loads a resource and exposes loading, success and error states plus a retry.
 * `load` must be referentially stable (a module-level function or a useCallback).
 */
export function useRemoteResource<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<ResourceState<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setState({ status: "success", data });
      },
      (error: unknown) => {
        if (!controller.signal.aborted) setState({ status: "error", error: toApiError(error) });
      },
    );
    return () => controller.abort();
  }, [load, attempt]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((value) => value + 1);
  }, []);

  return { state, reload };
}
