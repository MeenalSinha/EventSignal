/** Phase 4: AssessmentPanel — full explainable assessment of an opportunity.
 *
 * Displays:
 *  - Overall score ring
 *  - Dimension scores (completeness, quality, consistency) with explanations
 *  - Missing critical / optional field lists
 *  - Ambiguous / conflicting field lists
 *  - Assessment limitations paragraph
 *  - Evidence snapshot counters
 */

import { useState } from "react";
import type { OpportunityAssessment } from "../types/assessment";
import { runAssessment } from "../services/assessmentService";
import { ScoreBar } from "./ScoreBar";

interface Props {
  opportunityId: string;
  opportunityTitle: string | null;
}

function OverallScoreRing({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  // SVG ring using stroke-dasharray trick
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const fill = circumference * score;
  const color = score >= 0.8 ? "#10b981" : score >= 0.55 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width="72" height="72" viewBox="0 0 72 72" aria-hidden="true">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="#d5dde6" strokeWidth="6" />
        <circle
          cx="36"
          cy="36"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={`${fill} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 36 36)"
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
        <text
          x="36"
          y="40"
          textAnchor="middle"
          fontSize="14"
          fontWeight="700"
          fill={color}
          fontFamily="system-ui"
        >
          {pct}%
        </text>
      </svg>
      <span className="mt-1 text-xs font-medium text-ink-soft">Overall</span>
    </div>
  );
}

function FieldChip({ name, tone }: { name: string; tone: "danger" | "warn" | "neutral" }) {
  const cls =
    tone === "danger"
      ? "bg-red-50 text-red-700 ring-red-600/20"
      : tone === "warn"
        ? "bg-amber-50 text-amber-800 ring-amber-600/20"
        : "bg-gray-50 text-gray-600 ring-gray-500/20";
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-mono ring-1 ring-inset ${cls}`}
    >
      {name}
    </span>
  );
}

export function AssessmentPanel({ opportunityId, opportunityTitle }: Props) {
  const [assessment, setAssessment] = useState<OpportunityAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAssess = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runAssessment(opportunityId);
      setAssessment(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Assessment failed.");
    } finally {
      setLoading(false);
    }
  };

  if (!assessment) {
    return (
      <div className="mt-3 flex items-center gap-3">
        <button
          id={`assess-btn-${opportunityId}`}
          type="button"
          onClick={handleAssess}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-md border border-teal bg-teal-wash px-3 py-1.5 text-xs font-medium text-teal-deep hover:bg-teal/10 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <>
              <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-teal border-t-transparent" />
              Evaluating…
            </>
          ) : (
            "Evaluate Opportunity"
          )}
        </button>
        {error && <p className="text-xs text-alert">{error}</p>}
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-xl border border-line bg-mist p-5 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-display text-sm font-semibold text-ink">
              Evidence Assessment
            </h4>
            <span className="rounded bg-teal-wash px-1.5 py-0.5 text-[10px] font-mono text-teal-deep border border-teal/20">
              Policy v{assessment.policy_version}
            </span>
          </div>
          <p className="text-xs text-ink-soft mt-0.5">
            {opportunityTitle ?? "This opportunity"} · AI extracts. Rules evaluate. Evidence explains.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <OverallScoreRing score={assessment.overall_score} />
          <button
            type="button"
            onClick={handleAssess}
            disabled={loading}
            title="Re-run assessment"
            className="rounded p-1 text-xs text-ink-soft hover:text-ink hover:bg-line transition-colors disabled:opacity-50"
          >
            ↺
          </button>
        </div>
      </div>

      {/* Evidence snapshot counters */}
      <div className="grid grid-cols-3 gap-2 rounded-lg border border-line bg-paper p-3 text-center text-xs">
        <div>
          <p className="text-xl font-bold text-emerald-600">{assessment.fields_found_count}</p>
          <p className="text-ink-soft">Fields found</p>
        </div>
        <div>
          <p className="text-xl font-bold text-gray-400">{assessment.fields_not_found_count}</p>
          <p className="text-ink-soft">Not found</p>
        </div>
        <div>
          <p className="text-xl font-bold text-red-400">{assessment.fields_failed_count}</p>
          <p className="text-ink-soft">Failed</p>
        </div>
      </div>

      {/* Dimension scores */}
      <div className="space-y-4">
        <ScoreBar
          label="Completeness"
          score={assessment.completeness_score}
          explanation={assessment.completeness_explanation}
        />
        <ScoreBar
          label="Evidence Quality"
          score={assessment.evidence_quality_score}
          explanation={assessment.evidence_quality_explanation}
        />
        <ScoreBar
          label="Consistency"
          score={assessment.consistency_score}
          explanation={assessment.consistency_explanation}
        />
      </div>

      {/* Missing critical fields */}
      {assessment.missing_critical_fields.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold text-alert">
            Missing critical fields ({assessment.missing_critical_fields.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {assessment.missing_critical_fields.map((f) => (
              <FieldChip key={f} name={f} tone="danger" />
            ))}
          </div>
        </div>
      )}

      {/* Missing optional fields */}
      {assessment.missing_optional_fields.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold text-caution">
            Missing optional fields ({assessment.missing_optional_fields.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {assessment.missing_optional_fields.map((f) => (
              <FieldChip key={f} name={f} tone="warn" />
            ))}
          </div>
        </div>
      )}

      {/* Ambiguous / verification */}
      {assessment.ambiguous_fields.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold text-caution">Needs verification</p>
          <div className="flex flex-wrap gap-1.5">
            {assessment.ambiguous_fields.map((f) => (
              <FieldChip key={f} name={f} tone="warn" />
            ))}
          </div>
        </div>
      )}

      {/* Conflicting sources detail */}
      {assessment.conflicting_fields.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-alert">
            Cross-source conflicts ({assessment.conflicting_fields.length})
          </p>
          {assessment.conflict_details.length > 0 ? (
            <div className="space-y-2">
              {assessment.conflict_details.map((cd) => (
                <div
                  key={cd.field_name}
                  className="rounded-lg border border-red-200 bg-red-50/50 p-3 text-xs"
                >
                  <p className="font-semibold text-red-800">
                    Field: <span className="font-mono">{cd.field_name}</span>
                  </p>
                  <p className="text-ink-soft mt-0.5">{cd.explanation}</p>
                  <div className="mt-2 space-y-1.5">
                    {Object.entries(cd.competing_values).map(([src, claim]) => (
                      <div
                        key={src}
                        className="rounded border border-line bg-paper p-2 text-[11px]"
                      >
                        <p className="font-medium text-ink truncate">Source: {src}</p>
                        <p className="text-teal-deep font-semibold mt-0.5">
                          Extracted: &ldquo;{claim.value}&rdquo;
                        </p>
                        {claim.supporting_excerpt && (
                          <p className="text-ink-soft italic mt-0.5">
                            Excerpt: &ldquo;{claim.supporting_excerpt}&rdquo;
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {assessment.conflicting_fields.map((f) => (
                <FieldChip key={f} name={f} tone="danger" />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Limitations */}
      <details className="rounded-lg border border-line bg-paper">
        <summary className="cursor-pointer px-4 py-2 text-xs font-medium text-ink-soft hover:text-ink select-none">
          Assessment limitations &amp; caveats
        </summary>
        <p className="px-4 pb-3 pt-1 text-xs leading-relaxed text-ink-soft">
          {assessment.limitations}
        </p>
      </details>
    </div>
  );
}
