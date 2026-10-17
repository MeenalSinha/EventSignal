import { useState } from "react";
import { ingestOpportunity } from "../services/opportunityService";
import type { OpportunityIngestResponse } from "../types/opportunity";
import { EvidenceBadge } from "./EvidenceBadge";

interface Props {
  onIngestSuccess?: (result: OpportunityIngestResponse) => void;
  onClose?: () => void;
}

export function OpportunityIntakeForm({ onIngestSuccess, onClose }: Props) {
  const [url, setUrl] = useState("");
  const [forceRefresh, setForceRefresh] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OpportunityIngestResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUrl = url.trim();
    if (!cleanUrl) {
      setError("Please enter a valid opportunity URL.");
      return;
    }
    if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
      setError("URL must start with http:// or https://");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await ingestOpportunity({ url: cleanUrl, force_refresh: forceRefresh });
      setResult(response);
      if (onIngestSuccess) {
        onIngestSuccess(response);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to ingest opportunity. Please check the URL and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setUrl("");
    setError(null);
    setResult(null);
    setForceRefresh(false);
  };

  return (
    <div className="rounded-xl border border-line bg-paper p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-display text-lg font-semibold text-ink">Opportunity Intake</h3>
          <p className="mt-1 text-sm text-ink-soft">
            Submit any public opportunity link. The backend retrieves the webpage safely, extracts published
            information, and records field-level evidence.
          </p>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-ink-soft hover:bg-paper-soft hover:text-ink"
            aria-label="Close intake"
          >
            ✕
          </button>
        )}
      </div>

      {!result && (
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label htmlFor="opportunity-url" className="block text-sm font-medium text-ink">
              Opportunity URL
            </label>
            <input
              id="opportunity-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/hackathon-2026"
              disabled={submitting}
              className="mt-1 block w-full rounded-md border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-ink-soft focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink disabled:opacity-50"
              required
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              id="force-refresh"
              type="checkbox"
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
              disabled={submitting}
              className="h-4 w-4 rounded border-line text-ink focus:ring-ink"
            />
            <label htmlFor="force-refresh" className="text-xs text-ink-soft">
              Force re-extraction if this URL was already ingested
            </label>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
              <p className="font-medium">Ingestion failed</p>
              <p className="mt-1 text-xs">{error}</p>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center rounded-md bg-ink px-4 py-2 text-sm font-medium text-canvas hover:bg-ink-soft focus:outline-none focus:ring-2 focus:ring-ink focus:ring-offset-2 disabled:opacity-50"
            >
              {submitting ? "Retrieving & Analyzing..." : "Analyze & Ingest Opportunity"}
            </button>
            {error && (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="text-xs text-ink underline hover:text-ink-soft"
              >
                Retry
              </button>
            )}
          </div>
        </form>
      )}

      {result && (
        <div className="mt-6 space-y-6">
          <div
            className={`rounded-md p-4 ${
              result.is_duplicate ? "bg-amber-50 text-amber-800" : "bg-emerald-50 text-emerald-800"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">
                  {result.is_duplicate ? "Existing Opportunity Returned" : "Opportunity Ingested Successfully"}
                </p>
                <p className="mt-1 text-xs">{result.message}</p>
                <p className="mt-1 text-xs">
                  {result.fields_extracted_count} field(s) genuinely evidenced from source.
                </p>
              </div>
              <button
                type="button"
                onClick={handleReset}
                className="rounded-md border border-line bg-paper px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper-soft"
              >
                Ingest Another
              </button>
            </div>
          </div>

          {/* Opportunity Details Card */}
          <div className="rounded-lg border border-line bg-canvas p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 className="font-display text-lg font-bold text-ink">
                  {result.opportunity.title ?? "Untitled Opportunity"}
                </h4>
                <p className="text-sm text-ink-soft">{result.opportunity.organizer ?? "Organizer not stated"}</p>
              </div>
              {result.opportunity.opportunity_type && (
                <span className="inline-flex rounded-full bg-paper px-2.5 py-1 text-xs font-semibold capitalize text-ink shadow-sm ring-1 ring-inset ring-line">
                  {result.opportunity.opportunity_type}
                </span>
              )}
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
              <div>
                <span className="font-medium text-ink-soft">Mode: </span>
                <span className="capitalize text-ink">{result.opportunity.mode ?? "Not specified"}</span>
              </div>
              <div>
                <span className="font-medium text-ink-soft">Location: </span>
                <span className="text-ink">{result.opportunity.location ?? "Not specified"}</span>
              </div>
              <div>
                <span className="font-medium text-ink-soft">Registration Deadline: </span>
                <span className="text-ink">
                  {result.opportunity.registration_deadline
                    ? new Date(result.opportunity.registration_deadline).toLocaleDateString()
                    : "Not published"}
                </span>
              </div>
              <div>
                <span className="font-medium text-ink-soft">Event Dates: </span>
                <span className="text-ink">
                  {result.opportunity.start_date
                    ? new Date(result.opportunity.start_date).toLocaleDateString()
                    : "Not published"}
                </span>
              </div>
              {result.opportunity.application_url && (
                <div className="sm:col-span-2">
                  <span className="font-medium text-ink-soft">Action Link: </span>
                  <a
                    href={result.opportunity.application_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-blue-600 underline hover:text-blue-800"
                  >
                    {result.opportunity.application_url}
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Source Provenance */}
          <div className="rounded-lg border border-line bg-canvas p-4 text-xs text-ink-soft">
            <p className="font-medium text-ink">Source Provenance</p>
            <p className="mt-1 break-all">
              <span className="font-medium">URL: </span>
              {result.source_reference.url}
            </p>
            {result.source_reference.content_hash && (
              <p className="mt-1 font-mono text-[11px]">
                <span className="font-sans font-medium">SHA256: </span>
                {result.source_reference.content_hash}
              </p>
            )}
          </div>

          {/* Field Evidence Breakdown */}
          <div>
            <h4 className="mb-2 font-display text-sm font-semibold text-ink">Field-Level Evidence Breakdown</h4>
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="min-w-full divide-y divide-line text-left text-xs">
                <thead className="bg-paper-soft text-ink-soft">
                  <tr>
                    <th className="px-3 py-2 font-medium">Field</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                    <th className="px-3 py-2 font-medium">Extracted Value</th>
                    <th className="px-3 py-2 font-medium">Supporting Source Excerpt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line bg-paper">
                  {result.evidence.map((ev) => (
                    <tr key={ev.id}>
                      <td className="whitespace-nowrap px-3 py-2 font-mono font-medium text-ink">{ev.field_name}</td>
                      <td className="whitespace-nowrap px-3 py-2">
                        <EvidenceBadge status={ev.evidence_status} />
                      </td>
                      <td className="px-3 py-2 text-ink">
                        {ev.extracted_value ?? <span className="italic text-ink-soft">—</span>}
                      </td>
                      <td className="max-w-xs truncate px-3 py-2 text-ink-soft" title={ev.supporting_excerpt ?? ""}>
                        {ev.supporting_excerpt ?? <span className="italic text-ink-soft">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
