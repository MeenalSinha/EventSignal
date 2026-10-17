import { useState } from "react";
import type { ResourceState } from "../hooks/useRemoteResource";
import type { EventList } from "../types/events";
import { AssessmentPanel } from "./AssessmentPanel";
import { OpportunityIntakeForm } from "./OpportunityIntakeForm";
import { StatePanel } from "./StatePanel";

interface Props {
  state: ResourceState<EventList>;
  onRetry: () => void;
}

export function EventWorkspace({ state, onRetry }: Props) {
  const [showIntake, setShowIntake] = useState(false);

  return (
    <section aria-labelledby="workspace-heading">
      <div className="mb-3 flex items-center justify-between">
        <h2 id="workspace-heading" className="font-display text-xl font-semibold">
          Event workspace
        </h2>
        {state.status === "success" && (
          <button
            type="button"
            onClick={() => setShowIntake(!showIntake)}
            className="rounded-md border border-line bg-paper px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper-soft"
          >
            {showIntake ? "Close Intake" : "Submit Opportunity URL"}
          </button>
        )}
      </div>

      {showIntake && (
        <div className="mb-6">
          <OpportunityIntakeForm
            onIngestSuccess={() => {
              onRetry();
            }}
            onClose={() => setShowIntake(false)}
          />
        </div>
      )}

      {state.status === "loading" && <StatePanel tone="loading" title="Loading your events" />}

      {state.status === "error" && (
        <StatePanel
          tone="error"
          title="Your events could not be loaded"
          action={{ label: "Try again", onClick: onRetry }}
        >
          <p>{state.error.message}</p>
        </StatePanel>
      )}

      {state.status === "success" && state.data.total === 0 && (
        <StatePanel tone="empty" title="The workspace is ready, with no events yet">
          <p>
            Events and opportunities you add will appear here with the evidence behind each detail. Click Submit
            Opportunity URL to extract and evaluate a public link.
          </p>
        </StatePanel>
      )}

      {state.status === "success" && state.data.total > 0 && (
        <div className="rounded-lg border border-line bg-paper p-6">
          <p className="text-sm text-ink-soft">
            {state.data.total === 1 ? "1 event stored" : `${state.data.total} events stored`}
            {state.data.items.length < state.data.total && `, showing the first ${state.data.items.length}`}
          </p>
          <ul className="mt-3 divide-y divide-line">
            {state.data.items.map((event) => (
              <li key={event.id} className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium text-ink">{event.event_name ?? event.title ?? "Untitled event"}</p>
                    <p className="text-sm text-ink-soft">{event.organizer ?? "Organizer not stated"}</p>
                  </div>
                </div>
                <AssessmentPanel
                  opportunityId={event.id}
                  opportunityTitle={event.event_name ?? event.title ?? null}
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
