"""Phase 4: Opportunity assessment engine.

Evaluates a persisted opportunity against five explainable dimensions:

  1. Completeness      — fraction of expected fields that have values.
  2. Evidence quality  — weighted reliability of the extraction methods used.
  3. Consistency       — absence of source conflicts across FieldEvidence records.
  4. Missing fields    — which critical and optional fields are absent.
  5. Ambiguous/conflicting — which fields carry NEEDS_VERIFICATION or SOURCES_DISAGREE status.

Design principles:
  - Operates exclusively on persisted data: Opportunity + FieldEvidence rows.
  - No network calls; no LLM calls; no fabrication.
  - Every score and explanation is derived deterministically from the evidence layer.
  - Limitations are explicit when the system cannot distinguish absence-of-information
    from genuine absence of the attribute.
  - Replaces any prior assessment for the same opportunity (upsert semantics).

Entry point:
  assess_opportunity(opportunity_id, session) -> OpportunityAssessment
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.field_evidence import EvidenceStatus, ExtractionMethod, FieldEvidence
from app.models.opportunity import Opportunity
from app.models.opportunity_assessment import OpportunityAssessment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

# Fields whose absence materially limits a student's ability to evaluate and act
# on the opportunity.
CRITICAL_FIELDS: frozenset[str] = frozenset(
    {
        "title",
        "opportunity_type",
        "organizer",
        "registration_deadline",
        "application_url",
    }
)

# Fields that are useful but whose absence does not block evaluation.
OPTIONAL_FIELDS: frozenset[str] = frozenset(
    {
        "start_date",
        "end_date",
        "submission_deadline",
        "location",
        "mode",
        "eligibility",
        "skills_required",
        "compensation",
    }
)

ALL_EXPECTED_FIELDS: frozenset[str] = CRITICAL_FIELDS | OPTIONAL_FIELDS

# Quality weights for extraction methods (higher = more reliable).
_METHOD_QUALITY: dict[ExtractionMethod, float] = {
    ExtractionMethod.STRUCTURED: 1.0,   # JSON-LD / Schema.org
    ExtractionMethod.RULE_BASED: 0.75,  # Pattern match / heuristics
    ExtractionMethod.MANUAL: 1.0,       # Human-entered
    ExtractionMethod.LLM: 0.5,          # LLM; requires review
}


# ---------------------------------------------------------------------------
# Internal result dataclass
# ---------------------------------------------------------------------------

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
    limitations: str = ""
    total_fields_assessed: int = 0
    fields_found_count: int = 0
    fields_not_found_count: int = 0
    fields_failed_count: int = 0


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _score_completeness(evidence_by_field: dict[str, FieldEvidence]) -> tuple[float, str]:
    """Return (score, explanation) for information completeness."""
    found_fields: set[str] = set()
    not_found_fields: set[str] = set()

    for field_name, ev in evidence_by_field.items():
        if field_name not in ALL_EXPECTED_FIELDS:
            continue
        if ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}:
            found_fields.add(field_name)
        elif ev.evidence_status in {
            EvidenceStatus.NOT_FOUND,
            EvidenceStatus.EXTRACTION_FAILED,
        }:
            not_found_fields.add(field_name)

    total = len(ALL_EXPECTED_FIELDS)
    found = len(found_fields)
    score = _clamp(found / total if total > 0 else 0.0)

    if score == 1.0:
        explanation = "All expected fields were found in the source."
    elif score >= 0.7:
        missing = sorted(ALL_EXPECTED_FIELDS - found_fields)
        explanation = (
            f"{found}/{total} expected fields found. "
            f"Missing: {', '.join(missing)}."
        )
    elif score >= 0.4:
        missing = sorted(ALL_EXPECTED_FIELDS - found_fields)
        explanation = (
            f"Only {found}/{total} expected fields found. "
            f"Significant gaps: {', '.join(missing)}. "
            "Verify the opportunity page directly before relying on extracted data."
        )
    else:
        missing = sorted(ALL_EXPECTED_FIELDS - found_fields)
        explanation = (
            f"Very low completeness: only {found}/{total} fields found. "
            f"Missing: {', '.join(missing)}. "
            "The source page may use a non-standard layout, or most details may "
            "not have been published yet."
        )

    return score, explanation


def _score_evidence_quality(
    evidence_by_field: dict[str, FieldEvidence],
) -> tuple[float, str]:
    """Return (score, explanation) for evidence reliability."""
    quality_values: list[float] = []
    method_counts: dict[str, int] = {}

    for field_name, ev in evidence_by_field.items():
        if field_name not in ALL_EXPECTED_FIELDS:
            continue
        if ev.evidence_status not in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}:
            continue
        q = _METHOD_QUALITY.get(ev.extraction_method, 0.5)
        quality_values.append(q)
        label = ev.extraction_method.value
        method_counts[label] = method_counts.get(label, 0) + 1

    if not quality_values:
        return 0.0, "No fields were successfully extracted; quality cannot be assessed."

    score = _clamp(sum(quality_values) / len(quality_values))

    method_summary = ", ".join(
        f"{count} via {method}" for method, count in sorted(method_counts.items())
    )

    if score >= 0.9:
        explanation = (
            f"High-quality evidence: extracted fields used reliable methods "
            f"({method_summary}). Structured data (JSON-LD/Schema.org) found."
        )
    elif score >= 0.7:
        explanation = (
            f"Good evidence quality ({method_summary}). Most fields use "
            "deterministic rule-based extraction from semantic HTML."
        )
    elif score >= 0.5:
        explanation = (
            f"Moderate evidence quality ({method_summary}). "
            "Some values rely on heuristic pattern matching — independent "
            "verification is recommended for time-sensitive details."
        )
    else:
        explanation = (
            f"Low evidence quality ({method_summary}). "
            "Extracted values depend on heuristics that may be imprecise. "
            "Treat all extracted information as preliminary."
        )

    return score, explanation


def _score_consistency(
    evidence_by_field: dict[str, FieldEvidence],
    source_count: int,
) -> tuple[float, str, list[str], list[str]]:
    """Return (score, explanation, ambiguous_fields, conflicting_fields)."""
    conflicting: list[str] = []
    ambiguous: list[str] = []

    for field_name, ev in evidence_by_field.items():
        if field_name not in ALL_EXPECTED_FIELDS:
            continue
        if ev.evidence_status == EvidenceStatus.SOURCES_DISAGREE:
            conflicting.append(field_name)
        elif ev.evidence_status == EvidenceStatus.NEEDS_VERIFICATION:
            ambiguous.append(field_name)

    if conflicting:
        score = _clamp(0.3 - 0.05 * len(conflicting))
        explanation = (
            f"{len(conflicting)} field(s) have conflicting values across sources: "
            f"{', '.join(sorted(conflicting))}. "
            "Do not rely on these values without verifying the primary source directly."
        )
    elif ambiguous:
        score = _clamp(0.7 - 0.05 * len(ambiguous))
        explanation = (
            f"{len(ambiguous)} field(s) require verification: "
            f"{', '.join(sorted(ambiguous))}. "
            "Values were found but could not be independently confirmed."
        )
    elif source_count == 1:
        score = 0.85
        explanation = (
            "No conflicts detected. Only one source was assessed, so cross-source "
            "consistency cannot be fully evaluated."
        )
    else:
        score = 1.0
        explanation = (
            f"All {source_count} sources agree on extracted values. "
            "No conflicts or ambiguities detected."
        )

    return score, explanation, sorted(ambiguous), sorted(conflicting)


def _build_limitations(
    missing_critical: list[str],
    missing_optional: list[str],
    source_count: int,
    structured_data_present: bool,
) -> str:
    parts: list[str] = []

    if missing_critical:
        parts.append(
            f"The following critical fields were not found and cannot be inferred: "
            f"{', '.join(missing_critical)}. "
            "Absence may mean the opportunity page did not publish this information, "
            "or that the extractor could not locate it in a non-standard layout."
        )

    if not structured_data_present:
        parts.append(
            "The source page did not contain structured data (JSON-LD or Schema.org). "
            "All values were extracted from unstructured HTML, which is more error-prone."
        )

    if source_count == 1:
        parts.append(
            "Only one source has been assessed. Multi-source verification and "
            "cross-reference consistency checks are not yet available."
        )

    if missing_optional:
        parts.append(
            f"Optional fields not found: {', '.join(missing_optional)}. "
            "These may be published on the primary opportunity page or linked documents."
        )

    if not parts:
        return (
            "No material limitations identified. Standard caveats apply: "
            "always verify critical details on the primary opportunity page "
            "before applying or registering."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def assess_opportunity(opportunity_id: str, session: Session) -> OpportunityAssessment:
    """Compute and persist an assessment for the given opportunity.

    Loads the opportunity's evidence records, applies all scoring dimensions,
    then upserts a single OpportunityAssessment record.

    Raises:
        LookupError: if the opportunity_id does not exist.
    """
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
    source_count = len(opp.sources)

    # Build field→evidence map (latest evidence per field)
    evidence_by_field: dict[str, FieldEvidence] = {}
    for ev in evidence_rows:
        evidence_by_field[ev.field_name] = ev

    # Detect whether structured data was used
    structured_data_present = any(
        ev.extraction_method == ExtractionMethod.STRUCTURED
        and ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
        for ev in evidence_rows
    )

    # --- Completeness dimension -------------------------------------------
    completeness_score, completeness_explanation = _score_completeness(evidence_by_field)

    # --- Evidence quality dimension ----------------------------------------
    evidence_quality_score, evidence_quality_explanation = _score_evidence_quality(
        evidence_by_field
    )

    # --- Consistency dimension --------------------------------------------
    consistency_score, consistency_explanation, ambiguous_fields, conflicting_fields = (
        _score_consistency(evidence_by_field, source_count)
    )

    # --- Field categorisation ---------------------------------------------
    missing_critical: list[str] = []
    missing_optional: list[str] = []

    for fname in sorted(CRITICAL_FIELDS):
        ev = evidence_by_field.get(fname)
        if ev is None or ev.evidence_status in {
            EvidenceStatus.NOT_FOUND,
            EvidenceStatus.NOT_ASSESSED,
            EvidenceStatus.EXTRACTION_FAILED,
        }:
            missing_critical.append(fname)

    for fname in sorted(OPTIONAL_FIELDS):
        ev = evidence_by_field.get(fname)
        if ev is None or ev.evidence_status in {
            EvidenceStatus.NOT_FOUND,
            EvidenceStatus.NOT_ASSESSED,
            EvidenceStatus.EXTRACTION_FAILED,
        }:
            missing_optional.append(fname)

    # --- Overall score (weighted average) ---------------------------------
    overall_score = _clamp(
        0.45 * completeness_score
        + 0.35 * evidence_quality_score
        + 0.20 * consistency_score
    )

    # --- Limitations paragraph ---------------------------------------------
    limitations = _build_limitations(
        missing_critical, missing_optional, source_count, structured_data_present
    )

    # --- Evidence snapshot counters ---------------------------------------
    assessed = [
        ev for ev in evidence_rows if ev.field_name in ALL_EXPECTED_FIELDS
    ]
    found_count = sum(
        1
        for ev in assessed
        if ev.evidence_status in {EvidenceStatus.FOUND, EvidenceStatus.MULTI_SOURCE}
    )
    not_found_count = sum(
        1
        for ev in assessed
        if ev.evidence_status in {EvidenceStatus.NOT_FOUND}
    )
    failed_count = sum(
        1
        for ev in assessed
        if ev.evidence_status == EvidenceStatus.EXTRACTION_FAILED
    )

    # --- Upsert assessment record ----------------------------------------
    session.execute(
        delete(OpportunityAssessment).where(
            OpportunityAssessment.opportunity_id == opportunity_id
        )
    )

    record = OpportunityAssessment(
        opportunity_id=opportunity_id,
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
        limitations=limitations,
        total_fields_assessed=len(assessed),
        fields_found_count=found_count,
        fields_not_found_count=not_found_count,
        fields_failed_count=failed_count,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    logger.info(
        "assessment.complete opportunity_id=%s overall=%.2f completeness=%.2f quality=%.2f",
        opportunity_id,
        overall_score,
        completeness_score,
        evidence_quality_score,
    )

    return record
