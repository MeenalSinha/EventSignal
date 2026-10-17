"""Gap-to-Helper matching engine.

Design contract:
  - Matching is purely rule-based. No ML inference, no probabilistic scoring,
    no fabricated explanations.
  - Every rule that fires is recorded in ``rule_results`` with its weight,
    contribution, and the actual attribute values that were compared.
  - The engine computes a float score in [0, 1]. Scores are ordinal indicators
    of relevance, not guarantees of suitability.
  - The engine records uncertainty notes for every match it cannot fully
    evaluate (e.g. delivery mode not specified).
  - Matching only runs against ACTIVE help offers.
  - A need must be OPEN to be eligible for matching.
  - Results are persisted as HelperMatch rows.

Scoring rules (v1):
  Rule 1 — Category alignment (weight 0.45)
    Exact match between need.category and offer.category.
    If matched: contribution = 0.45.

  Rule 2 — Delivery mode alignment (weight 0.20)
    If need.preferred_delivery_mode is set:
      Exact match with offer.delivery_mode → contribution = 0.20.
      No match → contribution = 0.
    If need.preferred_delivery_mode is None:
      No deduction, no contribution; recorded as "not evaluated".

  Rule 3 — Skill keyword overlap (weight 0.25)
    Tokenise need.description (lowercased words, stop-words stripped) and
    offer.applicable_skills (lowercased words).
    Overlap ratio = |intersection| / max(|need_tokens|, 1).
    Contribution = 0.25 × min(overlap_ratio, 1.0).

  Rule 4 — Urgency boost (weight 0.10)
    If need.urgency == HIGH → contribution = 0.10.
    If need.urgency == MEDIUM → contribution = 0.05.
    LOW → 0.

Final score = sum of contributions (capped at 1.0).

Only matches with score >= SCORE_THRESHOLD are persisted.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.help_offer import HelpOffer, HelpOfferStatus
from app.models.helper_match import HelperMatch, MatchStatus
from app.models.student_need import NeedStatus, NeedUrgency, StudentNeed

logger = logging.getLogger(__name__)

SCORER_VERSION = "v1.0"
SCORE_THRESHOLD = 0.10  # Minimum score to persist a match

_STOP_WORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "been", "by", "for",
        "from", "has", "have", "i", "in", "is", "it", "its", "of", "on",
        "or", "that", "the", "this", "to", "was", "were", "will", "with",
    }
)


def _tokenise(text: str | None) -> set[str]:
    """Lowercase, split, strip stop-words. Returns empty set for None/empty."""
    if not text:
        return set()
    return {w for w in text.lower().split() if w.isalpha() and w not in _STOP_WORDS}


def _compute_match(need: StudentNeed, offer: HelpOffer) -> dict[str, Any] | None:
    """Evaluate all rules for (need, offer) and return a match dict or None."""
    rule_results: list[dict[str, Any]] = []
    total_score = 0.0
    uncertainty_parts: list[str] = []

    # Rule 1 — Category alignment
    r1_matched = need.category.strip().lower() == offer.category.strip().lower()
    r1_contrib = 0.45 if r1_matched else 0.0
    total_score += r1_contrib
    rule_results.append(
        {
            "rule": "category_alignment",
            "matched": r1_matched,
            "weight": 0.45,
            "contribution": r1_contrib,
            "evidence": (
                f"Need category '{need.category}' {'matches' if r1_matched else 'does not match'}"
                f" offer category '{offer.category}'"
            ),
        }
    )

    # Rule 2 — Delivery mode alignment
    if need.preferred_delivery_mode:
        r2_matched = (
            need.preferred_delivery_mode.strip().lower()
            == offer.delivery_mode.strip().lower()
        )
        r2_contrib = 0.20 if r2_matched else 0.0
        total_score += r2_contrib
        rule_results.append(
            {
                "rule": "delivery_mode_alignment",
                "matched": r2_matched,
                "weight": 0.20,
                "contribution": r2_contrib,
                "evidence": (
                    f"Need delivery mode '{need.preferred_delivery_mode}' "
                    f"{'matches' if r2_matched else 'does not match'} "
                    f"offer delivery mode '{offer.delivery_mode}'"
                ),
            }
        )
    else:
        rule_results.append(
            {
                "rule": "delivery_mode_alignment",
                "matched": None,
                "weight": 0.20,
                "contribution": 0.0,
                "evidence": "Student did not specify a preferred delivery mode; rule not evaluated.",
            }
        )
        uncertainty_parts.append(
            "Student did not specify a preferred delivery mode. "
            "The delivery format suitability of this match cannot be confirmed."
        )

    # Rule 3 — Skill keyword overlap
    need_tokens = _tokenise(need.description)
    offer_tokens = _tokenise(offer.applicable_skills)
    if need_tokens and offer_tokens:
        overlap = need_tokens & offer_tokens
        overlap_ratio = len(overlap) / max(len(need_tokens), 1)
        r3_contrib = round(0.25 * min(overlap_ratio, 1.0), 4)
        total_score += r3_contrib
        rule_results.append(
            {
                "rule": "skill_keyword_overlap",
                "matched": bool(overlap),
                "weight": 0.25,
                "contribution": r3_contrib,
                "evidence": (
                    f"Shared keywords between need description and offer skills: "
                    f"{sorted(overlap) if overlap else 'none'}. "
                    f"Overlap ratio: {overlap_ratio:.2f}."
                ),
            }
        )
    else:
        rule_results.append(
            {
                "rule": "skill_keyword_overlap",
                "matched": None,
                "weight": 0.25,
                "contribution": 0.0,
                "evidence": (
                    "Insufficient text in need description or offer skills to evaluate "
                    "keyword overlap."
                ),
            }
        )
        uncertainty_parts.append(
            "Skill keyword overlap could not be evaluated due to insufficient text content."
        )

    # Rule 4 — Urgency boost
    urgency = need.urgency
    if urgency == NeedUrgency.HIGH:
        r4_contrib = 0.10
    elif urgency == NeedUrgency.MEDIUM:
        r4_contrib = 0.05
    else:
        r4_contrib = 0.0
    total_score += r4_contrib
    rule_results.append(
        {
            "rule": "urgency_boost",
            "matched": urgency in (NeedUrgency.HIGH, NeedUrgency.MEDIUM),
            "weight": 0.10,
            "contribution": r4_contrib,
            "evidence": f"Need urgency is '{urgency}'. Boost applied: {r4_contrib}.",
        }
    )

    final_score = min(round(total_score, 4), 1.0)

    if final_score < SCORE_THRESHOLD:
        return None

    # Build summary explanation from contributing rules.
    matched_rules = [r for r in rule_results if r["matched"]]
    if matched_rules:
        bullets = "; ".join(r["evidence"] for r in matched_rules)
        summary = (
            f"This offer was surfaced because: {bullets}. "
            f"Relevance score: {final_score:.2f} / 1.00 (computed by rule engine {SCORER_VERSION})."
        )
    else:
        summary = (
            f"This offer met the minimum relevance threshold ({SCORE_THRESHOLD}) "
            f"with a score of {final_score:.2f}, but no individual rule fired a strong positive "
            f"signal. Review carefully before acting on this suggestion."
        )

    uncertainty_notes = (
        " ".join(uncertainty_parts) if uncertainty_parts else None
    )

    return {
        "score": final_score,
        "rule_results": rule_results,
        "summary_explanation": summary,
        "uncertainty_notes": uncertainty_notes,
    }


def run_matching_for_need(
    db: Session,
    need: StudentNeed,
    *,
    replace_existing: bool = False,
) -> list[HelperMatch]:
    """Run the matching engine for a single StudentNeed.

    Args:
        db: Active database session.
        need: The OPEN StudentNeed to match against.
        replace_existing: If True, expire any PROPOSED matches for this need
            before computing new ones.

    Returns:
        List of newly persisted HelperMatch rows.
    """
    if need.status != NeedStatus.OPEN:
        raise ValueError(
            f"Matching can only run against OPEN needs; need '{need.id}' has status "
            f"'{need.status}'."
        )

    if replace_existing:
        existing = (
            db.query(HelperMatch)
            .filter(
                HelperMatch.need_id == need.id,
                HelperMatch.status == MatchStatus.PROPOSED,
            )
            .all()
        )
        for m in existing:
            m.status = MatchStatus.EXPIRED
            m.updated_at = datetime.now(UTC)

    # Load ACTIVE offers in the same institution as the need.
    offers: list[HelpOffer] = (
        db.query(HelpOffer)
        .filter(
            HelpOffer.institution_id == need.institution_id,
            HelpOffer.status == HelpOfferStatus.ACTIVE,
            HelpOffer.willing_to_help.is_(True),
        )
        .all()
    )

    new_matches: list[HelperMatch] = []
    for offer in offers:
        result = _compute_match(need, offer)
        if result is None:
            continue
        match = HelperMatch(
            need_id=need.id,
            help_offer_id=offer.id,
            institution_id=need.institution_id,
            score=result["score"],
            rule_results=result["rule_results"],
            summary_explanation=result["summary_explanation"],
            uncertainty_notes=result["uncertainty_notes"],
            scorer_version=SCORER_VERSION,
            status=MatchStatus.PROPOSED,
            is_seen=False,
        )
        db.add(match)
        new_matches.append(match)

    if new_matches:
        need.status = NeedStatus.MATCHED
        need.updated_at = datetime.now(UTC)

    db.flush()
    logger.info(
        "Matching engine: need '%s' → %d match(es) (scorer=%s, threshold=%.2f)",
        need.id,
        len(new_matches),
        SCORER_VERSION,
        SCORE_THRESHOLD,
    )
    return new_matches
