import type { ResourceState } from "../hooks/useRemoteResource";
import type { HealthResponse } from "../types/health";
import { ConnectionStatus, SIGNAL_RULE_STYLES, describeConnection } from "./ConnectionStatus";

export function Header({ health }: { health: ResourceState<HealthResponse> }) {
  const { tone } = describeConnection(health);
  return (
    <header className="bg-paper">
      {/* The rule beneath the header reflects the live backend state. */}
      <div aria-hidden="true" className={`h-[3px] w-full transition-colors ${SIGNAL_RULE_STYLES[tone]}`} />
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4 sm:px-8">
        <div className="flex items-center gap-3">
          <img src="/favicon.svg" alt="" width={32} height={32} className="rounded-md" />
          <span className="font-display text-xl font-semibold tracking-tight">EventSignal</span>
        </div>
        <ConnectionStatus state={health} />
      </div>
    </header>
  );
}
