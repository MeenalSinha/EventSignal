import type { ReactNode } from "react";

export type StateTone = "loading" | "error" | "warning" | "empty";

interface StatePanelProps {
  tone: StateTone;
  title: string;
  children?: ReactNode;
  action?: { label: string; onClick: () => void };
}

const TONE_STYLES: Record<StateTone, string> = {
  loading: "border-line bg-paper",
  empty: "border-dashed border-line bg-paper",
  warning: "border-caution/40 bg-caution-wash",
  error: "border-alert/40 bg-alert-wash",
};

/** One reusable block for loading, empty, warning and error states. */
export function StatePanel({ tone, title, children, action }: StatePanelProps) {
  const role = tone === "error" ? "alert" : tone === "loading" ? "status" : undefined;
  return (
    <div role={role} className={`rounded-lg border p-6 ${TONE_STYLES[tone]}`}>
      <div className="flex items-start gap-3">
        {tone === "loading" && (
          <span
            aria-hidden="true"
            className="mt-1 size-4 shrink-0 animate-spin rounded-full border-2 border-line border-t-teal motion-reduce:animate-none"
          />
        )}
        <div className="min-w-0">
          <h3 className="font-display text-lg font-semibold leading-snug">{title}</h3>
          {children && <div className="mt-2 max-w-prose text-[0.95rem] leading-relaxed text-ink-soft">{children}</div>}
          {action && (
            <button
              type="button"
              onClick={action.onClick}
              className="mt-4 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-paper transition-colors hover:bg-teal-deep"
            >
              {action.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
