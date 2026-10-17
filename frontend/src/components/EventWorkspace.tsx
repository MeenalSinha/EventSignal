import type { ResourceState } from "../hooks/useRemoteResource";
import type { EventList } from "../types/events";
import { StatePanel } from "./StatePanel";

interface Props {
  state: ResourceState<EventList>;
  onRetry: () => void;
}

export function EventWorkspace({ state, onRetry }: Props) {
  return (
    <section aria-labelledby="workspace-heading">
      <h2 id="workspace-heading" className="mb-3 font-display text-xl font-semibold">
        Event workspace
      </h2>

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
            Events you add will appear here with the evidence behind each detail. Adding events is not available in this
            version, so there is nothing to show yet.
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
              <li key={event.id} className="py-3">
                <p className="font-medium">{event.event_name ?? "Untitled event"}</p>
                <p className="text-sm text-ink-soft">{event.organizer ?? "Organizer not stated"}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
