import type { ResourceState } from "../hooks/useRemoteResource";
import type { HealthResponse } from "../types/health";
import type { UserProfile } from "../types/auth";
import { ConnectionStatus, SIGNAL_RULE_STYLES, describeConnection } from "./ConnectionStatus";

interface HeaderProps {
  health: ResourceState<HealthResponse>;
  currentView?: "opportunities" | "institutions";
  onViewChange?: (view: "opportunities" | "institutions") => void;
  currentUser?: UserProfile | null;
  onOpenAuth?: () => void;
}

export function Header({
  health,
  currentView = "opportunities",
  onViewChange,
  currentUser = null,
  onOpenAuth,
}: HeaderProps) {
  const { tone } = describeConnection(health);
  return (
    <header className="bg-paper">
      {/* The rule beneath the header reflects the live backend state. */}
      <div aria-hidden="true" className={`h-[3px] w-full transition-colors ${SIGNAL_RULE_STYLES[tone]}`} />
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4 sm:px-8">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <img src="/favicon.svg" alt="" width={32} height={32} className="rounded-md" />
            <span className="font-display text-xl font-semibold tracking-tight">EventSignal</span>
          </div>

          {onViewChange && (
            <div className="hidden sm:flex items-center gap-1 rounded-xl bg-paper-warm p-1 text-xs font-semibold">
              <button
                onClick={() => onViewChange("opportunities")}
                className={`rounded-lg px-3 py-1.5 transition ${
                  currentView === "opportunities"
                    ? "bg-paper text-ink shadow-sm"
                    : "text-ink-soft hover:text-ink"
                }`}
              >
                Opportunities & Evidence
              </button>
              <button
                onClick={() => onViewChange("institutions")}
                className={`rounded-lg px-3 py-1.5 transition ${
                  currentView === "institutions"
                    ? "bg-paper text-ink shadow-sm"
                    : "text-ink-soft hover:text-ink"
                }`}
              >
                College Workspaces
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {onOpenAuth && (
            <button
              onClick={onOpenAuth}
              className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-paper px-3 py-1.5 text-xs font-semibold text-ink transition hover:bg-paper-warm"
            >
              {currentUser ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span>{currentUser.user.full_name}</span>
                </>
              ) : (
                <>
                  <span>👤 Sign In / Register</span>
                </>
              )}
            </button>
          )}

          <ConnectionStatus state={health} />
        </div>
      </div>

      {/* Mobile nav switcher */}
      {onViewChange && (
        <div className="flex sm:hidden border-b border-line bg-paper-warm p-1 text-xs font-semibold">
          <button
            onClick={() => onViewChange("opportunities")}
            className={`flex-1 py-1.5 text-center transition ${
              currentView === "opportunities" ? "bg-paper text-ink shadow-sm" : "text-ink-soft"
            }`}
          >
            Opportunities
          </button>
          <button
            onClick={() => onViewChange("institutions")}
            className={`flex-1 py-1.5 text-center transition ${
              currentView === "institutions" ? "bg-paper text-ink shadow-sm" : "text-ink-soft"
            }`}
          >
            College Workspaces
          </button>
        </div>
      )}
    </header>
  );
}
