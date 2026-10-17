import type { ResourceState } from "../hooks/useRemoteResource";
import type { HealthResponse } from "../types/health";

export type ConnectionTone = "checking" | "connected" | "problem" | "offline";

export function describeConnection(state: ResourceState<HealthResponse>): { tone: ConnectionTone; label: string } {
  switch (state.status) {
    case "loading":
      return { tone: "checking", label: "Checking backend" };
    case "error":
      return { tone: "offline", label: "Cannot connect to backend" };
    case "success":
      return state.data.status === "healthy"
        ? { tone: "connected", label: "Backend connected" }
        : { tone: "problem", label: `Backend ${state.data.status}` };
  }
}

const PILL_STYLES: Record<ConnectionTone, string> = {
  checking: "border-line bg-paper text-ink-soft",
  connected: "border-teal/40 bg-teal-wash text-teal-deep",
  problem: "border-caution/40 bg-caution-wash text-caution",
  offline: "border-alert/40 bg-alert-wash text-alert",
};

const DOT_STYLES: Record<ConnectionTone, string> = {
  checking: "bg-ink-soft/50",
  connected: "bg-teal",
  problem: "bg-caution",
  offline: "bg-alert",
};

export const SIGNAL_RULE_STYLES: Record<ConnectionTone, string> = {
  checking: "bg-line",
  connected: "bg-teal",
  problem: "bg-caution",
  offline: "bg-alert",
};

/** Status text always accompanies the colour, so meaning never depends on colour alone. */
export function ConnectionStatus({ state }: { state: ResourceState<HealthResponse> }) {
  const { tone, label } = describeConnection(state);
  return (
    <p
      role="status"
      data-tone={tone}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium ${PILL_STYLES[tone]}`}
    >
      <span aria-hidden="true" className={`size-2 rounded-full ${DOT_STYLES[tone]}`} />
      {label}
    </p>
  );
}
