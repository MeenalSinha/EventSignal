"""Phase 4: Opportunity assessment engine.

Evaluates an ingested opportunity against explainable dimensions according
to a validated, declarative AssessmentPolicy:

  1. Completeness      — weighted fraction of applicable fields established.
  2. Evidence quality  — weighted reliability of extraction methods used.
  3. Consistency       — cross-source consistency / absence of conflicts.
  4. Missing fields    — explicit classification of missing critical vs optional.
  5. Uncertainty       — transparent disclosure of limitations and single-source caveats.

Design principles:
  - Operates exclusively on persisted data: Opportunity, SourceReference, FieldEvidence.
  - Business rules, weights, and applicability rules are driven by AssessmentPolicy.
  - Modifying the policy configuration changes assessment results without code modifications.
  - Fully supports multi-source evaluation and detailed conflict analysis.
  - No network calls, no LLM hallucinations, deterministic and explainable.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.assessment_policy import AssessmentPolicy, load_assessment_policy
from app.models.field_evidence import EvidenceStatus, ExtractionMethod, FieldEvidence
from app.models.opportunity import Opportunity
from app.models.opportunity_assessment import OpportunityAssessment
from app.models.source_reference import SourceReference

logger = logging.getLogger(__name__)

# Defaults for backward compatibility
CRITICAL_FIELDS: frozenset[str] = frozenset(
    [
        "title",
        "opportunity_type",
        "organizer",
        "registration_deadline",
        "application_url",
    ]
)
OPTIONAL_FIELDS: frozenset[str] = frozenset(
    [
        "start_date",
        "end_date",
        "submission_deadline",
        "location",
        "mode",
        "eligibility",
        "skills_required",
        "compensation",
    ]
)
ALL_EXPECTED_FIELDS: frozenset[str] = CRITICAL_FIELDS | OPTIONAL_FIELDS


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _normalize_for_comparison(val: str | None) -> str:
    """Normalize extracted strings for cross-source consistency comparison."""
    if val is None:
        return ""
    # Strip whitespace, lowercase, collapse internal whitespace
    return " ".join(val.strip().lower().split())


@dataclass
class _AssessmentResult:
    completeness_score: float
    evidence_quality_score: float
    consistency_score: float
    overall_score: float
    completeness_explanation: str
    evidence_quality_explanation: str
    consistency_explanation: str
    missing_critical_fields: list[str] = field(default_factory=list)
    missing_optional_fields: list[str] = field(default_factory=list)
    ambiguous_fields: list[str] = field(default_factory=list)
    conflicting_fields: list[str] = field(default_factory=list)
    conflict_details: list[dict[str, Any]] = field(default_factory=list)
    limitations: str = ""
    total_fields_assessed: int = 0
    fields_found_count: int = 0
    fields_not_found_count: int = 0
    fields_failed_count: int = 0


def _evaluate_completeness(
    evidence_by_field: dict[str, list[FieldEvidence]],
    applicable_critical: set[str],
    applicable_optional: set[str],
    policy: AssessmentPolicy,
) -> tuple[float, str, list[str], list[str]]:
    """Calculate completeness score and identify missing fields based on policy."""
    all_applicable = applicable_critical | applicable_optional
    missing_critical: list[str] = []
    missing_optional: list[str] = []

    total_weight = 0.0
    found_weight = 0.0

    for fname in sorted(applicable_critical):
        w = policy.field_weights.get(fname, 2.0)
        total_weight += w
        ev_list = evidence_by_field.get(fname, [])
        is_found = any(
            ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
            for ev in ev_list
        )
        if is_found:
            found_weight += w
        else:
            missing_critical.append(fname)

    for fname in sorted(applicable_optional):
        w = policy.field_weights.get(fname, 1.0)
        total_weight += w
        ev_list = evidence_by_field.get(fname, [])
        is_found = any(
            ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
            for ev in ev_list
        )
        if is_found:
            found_weight += w
        else:
            missing_optional.append(fname)

    if total_weight <= 0.0:
        return 0.0, "No applicable fields configured for this opportunity type.", [], []

    score = _clamp(found_weight / total_weight)
    found_count = len(all_applicable) - len(missing_critical) - len(missing_optional)
    total_count = len(all_applicable)

    if score >= 0.99:
        explanation = f"All {total_count} applicable fields were established with source evidence."
    elif score >= 0.70:
        missing = missing_critical + missing_optional
        explanation = (
            f"{found_count}/{total_count} applicable fields established. "
            f"Missing: {', '.join(missing)}."
        )
    elif score >= 0.40:
        missing = missing_critical + missing_optional
        explanation = (
            f"Only {found_count}/{total_count} applicable fields established. "
            f"Material gaps: {', '.join(missing)}. Verify the primary listing before registering."
        )
    else:
        missing = missing_critical + missing_optional
        explanation = (
            f"Low completeness: only {found_count}/{total_count} fields found. "
            f"Missing: {', '.join(missing)}."
        )

    return score, explanation, missing_critical, missing_optional


def _evaluate_evidence_quality(
    evidence_by_field: dict[str, list[FieldEvidence]],
    all_applicable: set[str],
    policy: AssessmentPolicy,
) -> tuple[float, str]:
    """Calculate evidence quality score weighted by extraction methods."""
    method_scores: list[float] = []
    method_counts: dict[str, int] = defaultdict(int)

    for fname in all_applicable:
        ev_list = evidence_by_field.get(fname, [])
        # Take the highest quality evidence record for each field
        valid_evs = [
            ev
            for ev in ev_list
            if ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
        ]
        if not valid_evs:
            continue

        best_q = 0.0
        best_method = ExtractionMethod.RULE_BASED
        for ev in valid_evs:
            q = policy.get_method_quality(ev.extraction_method)
            if q > best_q:
                best_q = q
                best_method = ev.extraction_method

        method_scores.append(best_q)
        method_counts[best_method.value] += 1

    if not method_scores:
        return 0.0, "No fields were successfully extracted; evidence quality cannot be assessed."

    score = _clamp(sum(method_scores) / len(method_scores))
    summary = ", ".join(f"{count} via {m}" for m, count in sorted(method_counts.items()))

    if score >= policy.thresholds.get("high_quality", 0.80):
        explanation = (
            f"High evidence quality ({summary}). Primary structured or verified extractions."
        )
    elif score >= policy.thresholds.get("moderate_quality", 0.55):
        explanation = (
            f"Good evidence quality ({summary}). Predominantly deterministic semantic extractions."
        )
    else:
        explanation = (
            f"Moderate or preliminary evidence quality ({summary}). "
            "Values rely on heuristics; independently verify key terms."
        )

    return score, explanation


def _evaluate_consistency(
    evidence_by_field: dict[str, list[FieldEvidence]],
    sources_by_id: dict[str, SourceReference],
    source_count: int,
    policy: AssessmentPolicy,
) -> tuple[float, str, list[str], list[str], list[dict[str, Any]]]:
    """Evaluate cross-source consistency and detect field-level conflicts."""
    conflicting_fields: list[str] = []
    ambiguous_fields: list[str] = []
    conflict_details: list[dict[str, Any]] = []

    for fname, ev_list in evidence_by_field.items():
        found_evs = [
            ev
            for ev in ev_list
            if ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
            and ev.extracted_value is not None
        ]

        if any(ev.evidence_status == EvidenceStatus.NEEDS_VERIFICATION for ev in ev_list):
            ambiguous_fields.append(fname)

        if (
            any(ev.evidence_status == EvidenceStatus.SOURCES_DISAGREE for ev in ev_list)
            and fname not in conflicting_fields
        ):
            conflicting_fields.append(fname)

        # Cross-source comparison across distinct sources
        distinct_source_values: dict[str, tuple[str, str | None]] = {}
        for ev in found_evs:
            src_key = ev.source_id or "unknown_source"
            if src_key not in distinct_source_values:
                distinct_source_values[src_key] = (
                    ev.extracted_value or "",
                    ev.supporting_excerpt,
                )

        if len(distinct_source_values) > 1:
            unique_norm_vals: dict[str, list[str]] = defaultdict(list)
            for src_key, (raw_val, _) in distinct_source_values.items():
                norm = _normalize_for_comparison(raw_val)
                unique_norm_vals[norm].append(src_key)

            if len(unique_norm_vals) > 1:
                # Contradiction detected between sources!
                if fname not in conflicting_fields:
                    conflicting_fields.append(fname)

                source_diffs: dict[str, Any] = {}
                for src_key, (raw_val, excerpt) in distinct_source_values.items():
                    src_ref = sources_by_id.get(src_key)
                    label = src_ref.url if src_ref and src_ref.url else src_key
                    source_diffs[label] = {
                        "value": raw_val,
                        "supporting_excerpt": excerpt,
                    }

                conflict_details.append(
                    {
                        "field_name": fname,
                        "sources_count": len(distinct_source_values),
                        "competing_values": source_diffs,
                        "explanation": (
                            f"Sources disagree on {fname}. "
                            f"{len(unique_norm_vals)} distinct values reported."
                        ),
                    }
                )

    # Compute consistency score
    if conflicting_fields:
        penalty_multiplier = policy.thresholds.get("conflict_penalty_multiplier", 0.05)
        conflict_base = policy.thresholds.get("conflict_base_score", 0.30)
        score = _clamp(conflict_base - (len(conflicting_fields) - 1) * penalty_multiplier)
        explanation = (
            f"Cross-source disagreement detected in {len(conflicting_fields)} field(s): "
            f"{', '.join(sorted(conflicting_fields))}. "
            "Conflicting values preserved with respective source provenance."
        )
    elif ambiguous_fields:
        score = 0.70
        explanation = (
            f"{len(ambiguous_fields)} field(s) require verification: "
            f"{', '.join(sorted(ambiguous_fields))}."
        )
    elif source_count == 1:
        single_source_penalty = policy.thresholds.get("single_source_penalty", 0.15)
        score = _clamp(1.0 - single_source_penalty)
        explanation = (
            "No conflicts detected. Single-source assessment; cross-source verification "
            "will activate when additional sources are attached."
        )
    else:
        score = 1.0
        explanation = (
            f"All {source_count} sources agree on established fields. "
            "No cross-source discrepancies found."
        )

    return (
        score,
        explanation,
        sorted(set(ambiguous_fields)),
        sorted(set(conflicting_fields)),
        conflict_details,
    )


def _build_limitations(
    missing_critical: list[str],
    missing_optional: list[str],
    source_count: int,
    conflicting_fields: list[str],
) -> str:
    """Build honest, transparent explanation of assessment limitations."""
    parts: list[str] = []

    if conflicting_fields:
        parts.append(
            f"Conflicting information exists across sources for {', '.join(conflicting_fields)}. "
            "Verify with the organizing entity directly."
        )

    if missing_critical:
        parts.append(
            f"Critical fields not established: {', '.join(missing_critical)}. "
            "Absence indicates information was either not published or not "
            "found in standard selectors."
        )

    if source_count == 1:
        parts.append(
            "Assessed from a single source reference. Cross-source corroboration is unavailable."
        )

    if missing_optional:
        parts.append(f"Optional fields unconfirmed: {', '.join(missing_optional)}.")

    if not parts:
        return (
            "Evidence fully corroborates established fields across multiple sources. "
            "Standard due diligence remains advised before applying."
        )

    return " ".join(parts)


def assess_opportunity(
    opportunity_id: str,
    session: Session,
    policy: AssessmentPolicy | None = None,
) -> OpportunityAssessment:
    """Compute and persist an explainable assessment for an opportunity.

    Operates deterministically from persisted records and validated policy.
    Uses upsert semantics to maintain 1:1 relationship with Opportunity.

    Raises:
        LookupError: if opportunity_id is not found.
    """
    if policy is None:
        policy = load_assessment_policy()

    opp = session.scalars(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(
            selectinload(Opportunity.evidence),
            selectinload(Opportunity.sources),
        )
    ).first()

    if opp is None:
        raise LookupError(f"Opportunity {opportunity_id!r} not found")

    evidence_rows: list[FieldEvidence] = list(opp.evidence)
    sources_by_id: dict[str, SourceReference] = {s.id: s for s in opp.sources}
    source_count = len(opp.sources)

    # Group evidence records by field name
    evidence_by_field: dict[str, list[FieldEvidence]] = defaultdict(list)
    for ev in evidence_rows:
        evidence_by_field[ev.field_name].append(ev)

    # Applicable fields per policy and opportunity type
    applicable_critical, applicable_optional = policy.get_applicable_fields(
        opp.opportunity_type.value if opp.opportunity_type else None
    )
    all_applicable = applicable_critical | applicable_optional

    # 1. Completeness dimension
    (
        completeness_score,
        completeness_explanation,
        missing_critical,
        missing_optional,
    ) = _evaluate_completeness(evidence_by_field, applicable_critical, applicable_optional, policy)

    # 2. Evidence quality dimension
    evidence_quality_score, evidence_quality_explanation = _evaluate_evidence_quality(
        evidence_by_field, all_applicable, policy
    )

    # 3. Consistency dimension & cross-source conflicts
    (
        consistency_score,
        consistency_explanation,
        ambiguous_fields,
        conflicting_fields,
        conflict_details,
    ) = _evaluate_consistency(evidence_by_field, sources_by_id, source_count, policy)

    # 4. Overall score (weighted by policy dimension weights)
    dw = policy.dimension_weights
    overall_score = _clamp(
        dw.get("completeness", 0.45) * completeness_score
        + dw.get("evidence_quality", 0.35) * evidence_quality_score
        + dw.get("consistency", 0.20) * consistency_score
    )

    # 5. Limitations disclosure
    limitations = _build_limitations(
        missing_critical, missing_optional, source_count, conflicting_fields
    )

    # Snapshot counters
    found_count = sum(
        1
        for fname in all_applicable
        if any(
            ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
            for ev in evidence_by_field.get(fname, [])
        )
    )
    not_found_count = len(all_applicable) - found_count
    failed_count = sum(
        1 for ev in evidence_rows if ev.evidence_status == EvidenceStatus.EXTRACTION_FAILED
    )

    # Atomic upsert
    session.execute(
        delete(OpportunityAssessment).where(OpportunityAssessment.opportunity_id == opportunity_id)
    )

    record = OpportunityAssessment(
        opportunity_id=opportunity_id,
        policy_version=policy.policy_version,
        overall_score=overall_score,
        completeness_score=completeness_score,
        evidence_quality_score=evidence_quality_score,
        consistency_score=consistency_score,
        completeness_explanation=completeness_explanation,
        evidence_quality_explanation=evidence_quality_explanation,
        consistency_explanation=consistency_explanation,
        missing_critical_fields=missing_critical,
        missing_optional_fields=missing_optional,
        ambiguous_fields=ambiguous_fields,
        conflicting_fields=conflicting_fields,
        conflict_details=conflict_details,
        limitations=limitations,
        total_fields_assessed=len(evidence_rows),
        fields_found_count=found_count,
        fields_not_found_count=not_found_count,
        fields_failed_count=failed_count,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    logger.info(
        "assessment.completed opportunity_id=%s overall=%.2f policy=%s",
        opportunity_id,
        overall_score,
        policy.policy_version,
    )
    return record
