import { useState } from "react";
import type { ResourceState } from "../hooks/useRemoteResource";
import type { ComponentStatus, HealthResponse } from "../types/health";
import { StatePanel } from "./StatePanel";

const COMPONENT_LABELS: Record<string, string> = { api: "API", database: "Database" };
const COMPONENT_STATUS_TEXT: Record<ComponentStatus, string> = {
  ok: "Working",
  degraded: "Degraded",
  unavailable: "Unavailable",
};
const COMPONENT_STATUS_STYLES: Record<ComponentStatus, string> = {
  ok: "text-teal-deep font-semibold",
  degraded: "text-caution font-semibold",
  unavailable: "text-alert font-semibold",
};

interface Props {
  state: ResourceState<HealthResponse>;
  onRetry: () => void;
}

function formatCheckedAt(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleTimeString();
}

export function ServiceStatusPanel({ state, onRetry }: Props) {
  const [isMinimized, setIsMinimized] = useState(false);

  const isHealthy =
    state.status === "success" &&
    state.data.status === "healthy" &&
    Object.values(state.data.components).every((c) => c.status === "ok");

  const isLoading = state.status === "loading";

  const dotColor = isHealthy ? "bg-teal" : isLoading ? "bg-amber-400" : "bg-alert";
  const pingColor = isHealthy ? "bg-teal/70" : isLoading ? "bg-amber-400/70" : "bg-alert/70";

  return (
    <aside
      aria-label="Service status monitor"
      className="fixed bottom-4 right-4 z-40 max-w-sm w-[calc(100vw-2rem)] sm:w-80 select-none shadow-2xl transition-all duration-200"
    >
      {isMinimized ? (
        <button
          type="button"
          onClick={() => setIsMinimized(false)}
          className="flex items-center gap-2 rounded-full border border-line bg-card/95 px-3 py-1.5 text-xs font-semibold text-ink shadow-lg backdrop-blur-md hover:border-teal hover:bg-page transition-all focus:outline-hidden"
          title="Click to view backend service status"
          aria-label="Expand service status"
        >
          <span className="relative flex h-2 w-2">
            <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${pingColor}`} />
            <span className={`relative inline-flex h-2 w-2 rounded-full ${dotColor}`} />
          </span>
          <span>{isHealthy ? "All systems normal" : isLoading ? "Checking services..." : "Service alert"}</span>
          <svg className="h-3.5 w-3.5 text-ink-soft shrink-0 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
          </svg>
        </button>
      ) : (
        <div className="rounded-xl border border-line bg-card/95 p-4 shadow-xl backdrop-blur-md text-xs">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-line pb-2.5">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${pingColor}`} />
                <span className={`relative inline-flex h-2 w-2 rounded-full ${dotColor}`} />
              </span>
              <h2 className="text-xs font-bold text-ink">Service status</h2>
            </div>
            <button
              type="button"
              onClick={() => setIsMinimized(true)}
              className="rounded p-1 text-ink-soft hover:bg-page hover:text-ink transition focus:outline-hidden"
              aria-label="Minimize service status"
              title="Minimize to floating pill"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Status Content */}
          <div className="pt-2.5">
            {state.status === "loading" && (
              <StatePanel tone="loading" title="Checking the backend" />
            )}

            {state.status === "error" && (
              <StatePanel
                tone="error"
                title="Cannot connect to the backend"
                action={{ label: "Retry connection", onClick: onRetry }}
              >
                <p className="text-xs">{state.error.message}</p>
                <p className="mt-1 text-[11px] text-ink-soft">
                  Make sure the API is running and that the frontend is configured with its address.
                </p>
              </StatePanel>
            )}

            {state.status === "success" && (
              <div className="space-y-2">
                <p className="text-[11px] text-ink-soft">{state.data.message}</p>
                <dl className="divide-y divide-line/60">
                  {Object.entries(state.data.components).map(([name, component]) => (
                    <div key={name} className="py-1.5 first:pt-0 flex items-center justify-between gap-2">
                      <dt className="font-medium text-ink">{COMPONENT_LABELS[name] ?? name}</dt>
                      <dd className={`text-[11px] ${COMPONENT_STATUS_STYLES[component.status]}`}>
                        {COMPONENT_STATUS_TEXT[component.status]}
                      </dd>
                    </div>
                  ))}
                </dl>
                {/* Details note */}
                <div className="text-[11px] text-ink-soft/90 space-y-0.5">
                  {Object.entries(state.data.components).map(([name, component]) => (
                    <p key={name} className="truncate text-[10px]">
                      {component.message}
                    </p>
                  ))}
                </div>
                <p className="border-t border-line/60 pt-2 text-[10px] text-ink-soft">
                  Version {state.data.version}, {state.data.environment} environment. Last checked{" "}
                  {formatCheckedAt(state.data.checked_at)}.
                </p>
                <button
                  type="button"
                  onClick={onRetry}
                  className="mt-2 w-full flex items-center justify-center gap-1.5 rounded-lg border border-line bg-page py-1.5 text-xs font-semibold text-ink transition hover:border-teal hover:text-teal-deep focus:outline-hidden"
                >
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Check again
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
