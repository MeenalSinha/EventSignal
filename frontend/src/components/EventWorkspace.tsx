import { useState } from "react";
import type { ResourceState } from "../hooks/useRemoteResource";
import type { EventList } from "../types/events";
import { attachOpportunitySource } from "../services/opportunityService";
import { AssessmentPanel } from "./AssessmentPanel";
import { OpportunityIntakeForm } from "./OpportunityIntakeForm";
import { StatePanel } from "./StatePanel";

interface Props {
  state: ResourceState<EventList>;
  onRetry: () => void;
}

export function EventWorkspace({ state, onRetry }: Props) {
  const [showIntake, setShowIntake] = useState(false);
  const [addingSourceForId, setAddingSourceForId] = useState<string | null>(null);
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [attachingSource, setAttachingSource] = useState(false);
  const [attachError, setAttachError] = useState<string | null>(null);

  const handleAttachSource = async (e: React.FormEvent, opportunityId: string) => {
    e.preventDefault();
    const cleanUrl = newSourceUrl.trim();
    if (!cleanUrl) return;

    setAttachingSource(true);
    setAttachError(null);
    try {
      await attachOpportunitySource(opportunityId, { url: cleanUrl });
      setNewSourceUrl("");
      setAddingSourceForId(null);
      onRetry();
    } catch (err: unknown) {
      setAttachError(err instanceof Error ? err.message : "Failed to attach source.");
    } finally {
      setAttachingSource(false);
    }
  };

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
                  <button
                    type="button"
                    onClick={() => {
                      setAddingSourceForId(addingSourceForId === event.id ? null : event.id);
                      setAttachError(null);
                      setNewSourceUrl("");
                    }}
                    className="rounded border border-line bg-paper px-2.5 py-1 text-xs font-medium text-ink-soft hover:text-ink hover:bg-paper-soft shrink-0"
                  >
                    {addingSourceForId === event.id ? "Cancel Add Source" : "+ Add Source"}
                  </button>
                </div>

                {addingSourceForId === event.id && (
                  <form onSubmit={(e) => handleAttachSource(e, event.id)} className="mt-3 rounded-lg border border-line bg-canvas p-3">
                    <p className="text-xs font-medium text-ink mb-1.5">Attach Additional Source to Opportunity</p>
                    <div className="flex items-center gap-2">
                      <input
                        type="url"
                        value={newSourceUrl}
                        onChange={(e) => setNewSourceUrl(e.target.value)}
                        placeholder="https://second-source.example.com/details"
                        disabled={attachingSource}
                        className="flex-1 rounded-md border border-line bg-paper px-3 py-1.5 text-xs text-ink placeholder:text-ink-soft focus:border-ink focus:outline-none"
                        required
                      />
                      <button
                        type="submit"
                        disabled={attachingSource || !newSourceUrl.trim()}
                        className="rounded-md border border-teal bg-teal-wash px-3 py-1.5 text-xs font-medium text-teal-deep hover:bg-teal/10 disabled:opacity-50"
                      >
                        {attachingSource ? "Attaching…" : "Attach"}
                      </button>
                    </div>
                    {attachError && <p className="mt-1.5 text-xs text-alert">{attachError}</p>}
                  </form>
                )}

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
