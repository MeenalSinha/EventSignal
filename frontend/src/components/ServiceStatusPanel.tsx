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
  ok: "text-teal-deep",
  degraded: "text-caution",
  unavailable: "text-alert",
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
  return (
    <section aria-labelledby="service-status-heading">
      <h2 id="service-status-heading" className="mb-3 font-display text-xl font-semibold">
        Service status
      </h2>

      {state.status === "loading" && <StatePanel tone="loading" title="Checking the backend" />}

      {state.status === "error" && (
        <StatePanel
          tone="error"
          title="Cannot connect to the backend"
          action={{ label: "Retry connection", onClick: onRetry }}
        >
          <p>{state.error.message}</p>
          <p className="mt-1">Make sure the API is running and that the frontend is configured with its address.</p>
        </StatePanel>
      )}

      {state.status === "success" && (
        <div className="rounded-lg border border-line bg-paper p-6">
          <p className="text-[0.95rem] text-ink-soft">{state.data.message}</p>
          <dl className="mt-4 divide-y divide-line text-sm">
            {Object.entries(state.data.components).map(([name, component]) => (
              <div key={name} className="py-3">
                <div className="flex items-baseline justify-between gap-4">
                  <dt className="font-medium">{COMPONENT_LABELS[name] ?? name}</dt>
                  <dd className={`font-semibold ${COMPONENT_STATUS_STYLES[component.status]}`}>
                    {COMPONENT_STATUS_TEXT[component.status]}
                  </dd>
                </div>
                <p className="mt-1 text-ink-soft">{component.message}</p>
              </div>
            ))}
          </dl>
          <p className="mt-2 border-t border-line pt-4 text-sm text-ink-soft">
            Version {state.data.version}, {state.data.environment} environment. Last checked{" "}
            {formatCheckedAt(state.data.checked_at)}.
          </p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-md border border-line px-4 py-2 text-sm font-semibold transition-colors hover:border-teal hover:text-teal-deep"
          >
            Check again
          </button>
        </div>
      )}
    </section>
  );
}
