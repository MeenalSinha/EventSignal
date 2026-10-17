"""Legacy handover service: create, update, submit, and acknowledge handovers.

Business rules enforced here:
  - Only the outgoing_user may edit or submit a DRAFT handover.
  - Only the incoming_user may acknowledge a SUBMITTED handover.
  - Submitting a newer handover for the same position supersedes all previous
    SUBMITTED/ACKNOWLEDGED handovers for that position.
  - Version numbers are auto-incremented per (position_id, institution_id).
  - Handover authors are identified by user_id; the service never assigns
    authorship without an authenticated principal.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.legacy_handover import HandoverStatus, LegacyHandover

logger = logging.getLogger(__name__)


def _next_version(db: Session, institution_id: str, position_id: str | None) -> int:
    """Return the next version number for a handover in this position."""
    if position_id is None:
        return 1
    latest = (
        db.query(LegacyHandover)
        .filter(
            LegacyHandover.institution_id == institution_id,
            LegacyHandover.position_id == position_id,
        )
        .order_by(LegacyHandover.version.desc())
        .first()
    )
    return (latest.version + 1) if latest else 1


def create_handover(
    db: Session,
    *,
    institution_id: str,
    outgoing_user_id: str,
    title: str,
    position_id: str | None = None,
    incoming_user_id: str | None = None,
    accomplishments_summary: str | None = None,
    ongoing_work: str | None = None,
    key_contacts: list[dict[str, Any]] | None = None,
    lessons_learned: str | None = None,
    recommended_first_steps: str | None = None,
) -> LegacyHandover:
    """Create a new DRAFT handover."""
    version = _next_version(db, institution_id, position_id)
    handover = LegacyHandover(
        institution_id=institution_id,
        position_id=position_id,
        outgoing_user_id=outgoing_user_id,
        incoming_user_id=incoming_user_id,
        title=title,
        accomplishments_summary=accomplishments_summary,
        ongoing_work=ongoing_work,
        key_contacts=key_contacts or [],
        lessons_learned=lessons_learned,
        recommended_first_steps=recommended_first_steps,
        version=version,
        status=HandoverStatus.DRAFT,
    )
    db.add(handover)
    db.flush()
    logger.info(
        "Handover '%s' created (v%d, position=%s, institution=%s)",
        handover.id,
        version,
        position_id,
        institution_id,
    )
    return handover


def update_handover(
    db: Session,
    handover: LegacyHandover,
    *,
    requesting_user_id: str,
    **fields: Any,
) -> LegacyHandover:
    """Update DRAFT handover content. Only the outgoing_user may edit."""
    if handover.status != HandoverStatus.DRAFT:
        raise ValueError(
            f"Only DRAFT handovers may be edited; handover '{handover.id}' "
            f"has status '{handover.status}'."
        )
    if handover.outgoing_user_id != requesting_user_id:
        raise PermissionError("Only the outgoing role holder may edit this handover.")
    allowed = {
        "title",
        "incoming_user_id",
        "accomplishments_summary",
        "ongoing_work",
        "key_contacts",
        "lessons_learned",
        "recommended_first_steps",
    }
    for key, value in fields.items():
        if key in allowed:
            setattr(handover, key, value)
    handover.updated_at = datetime.now(UTC)
    db.flush()
    return handover


def submit_handover(
    db: Session,
    handover: LegacyHandover,
    *,
    requesting_user_id: str,
) -> LegacyHandover:
    """Submit a DRAFT handover, making it visible to the incoming holder.

    Supersedes previous SUBMITTED or ACKNOWLEDGED handovers for the same
    position within the institution.
    """
    if handover.status != HandoverStatus.DRAFT:
        raise ValueError(
            f"Only DRAFT handovers may be submitted; handover '{handover.id}' "
            f"has status '{handover.status}'."
        )
    if handover.outgoing_user_id != requesting_user_id:
        raise PermissionError("Only the outgoing role holder may submit this handover.")

    # Supersede older handovers for the same position.
    if handover.position_id:
        supersede_targets = (
            db.query(LegacyHandover)
            .filter(
                LegacyHandover.institution_id == handover.institution_id,
                LegacyHandover.position_id == handover.position_id,
                LegacyHandover.id != handover.id,
                LegacyHandover.status.in_([HandoverStatus.SUBMITTED, HandoverStatus.ACKNOWLEDGED]),
            )
            .all()
        )
        for old in supersede_targets:
            old.status = HandoverStatus.SUPERSEDED
            old.updated_at = datetime.now(UTC)

    handover.status = HandoverStatus.SUBMITTED
    handover.updated_at = datetime.now(UTC)
    db.flush()
    logger.info("Handover '%s' submitted.", handover.id)
    return handover


def acknowledge_handover(
    db: Session,
    handover: LegacyHandover,
    *,
    requesting_user_id: str,
) -> LegacyHandover:
    """Incoming holder acknowledges receipt and review of a SUBMITTED handover."""
    if handover.status != HandoverStatus.SUBMITTED:
        raise ValueError(
            f"Only SUBMITTED handovers may be acknowledged; handover '{handover.id}' "
            f"has status '{handover.status}'."
        )
    if handover.incoming_user_id != requesting_user_id:
        raise PermissionError(
            "Only the designated incoming role holder may acknowledge this handover."
        )
    handover.status = HandoverStatus.ACKNOWLEDGED
    handover.acknowledged_at = datetime.now(UTC)
    handover.updated_at = datetime.now(UTC)
    db.flush()
    logger.info("Handover '%s' acknowledged by '%s'.", handover.id, requesting_user_id)
    return handover
