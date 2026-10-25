"""Phase 7 API router: Gap-to-Helper Matching & EventSignal Legacy.

Endpoints:

  Needs
    POST   /institutions/{institution_id}/needs               - Declare a new need
    GET    /institutions/{institution_id}/needs               - List my needs
    GET    /institutions/{institution_id}/needs/{need_id}     - Get a need
    PATCH  /institutions/{institution_id}/needs/{need_id}     - Update a need
    POST   /institutions/{institution_id}/needs/{need_id}/run-matching - Trigger matching

  Matches
    GET    /institutions/{institution_id}/needs/{need_id}/matches      - List matches for a need
    GET    /institutions/{institution_id}/matches/{match_id}           - Get a match
    PATCH  /institutions/{institution_id}/matches/{match_id}/status    - Update match status

  Handovers
    POST   /institutions/{institution_id}/handovers                    - Create draft handover
    GET    /institutions/{institution_id}/handovers                    - List handovers
    GET    /institutions/{institution_id}/handovers/{handover_id}      - Get a handover
    PATCH  /institutions/{institution_id}/handovers/{handover_id}      - Update draft
    POST   /institutions/{institution_id}/handovers/{handover_id}/submit      - Submit
    POST   /institutions/{institution_id}/handovers/{handover_id}/acknowledge - Acknowledge

  Event Memories
    POST   /institutions/{institution_id}/memories             - Create memory record
    GET    /institutions/{institution_id}/memories             - List memories
    GET    /institutions/{institution_id}/memories/{memory_id} - Get a memory

  Follow-Up Tasks
    POST   /institutions/{institution_id}/tasks                - Create a task
    GET    /institutions/{institution_id}/tasks                - List my tasks
    GET    /institutions/{institution_id}/tasks/{task_id}      - Get a task
    PATCH  /institutions/{institution_id}/tasks/{task_id}      - Update a task
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_institution_membership
from app.database import get_db
from app.models.event_memory import EventMemory
from app.models.follow_up_task import FollowUpTask, TaskSource
from app.models.helper_match import HelperMatch, MatchStatus
from app.models.legacy_handover import LegacyHandover
from app.models.student_need import NeedStatus, StudentNeed
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.phase7 import (
    EventMemoryCreate,
    EventMemoryListResponse,
    EventMemoryRead,
    FollowUpTaskCreate,
    FollowUpTaskListResponse,
    FollowUpTaskRead,
    FollowUpTaskUpdate,
    HelperMatchListResponse,
    HelperMatchRead,
    HelperMatchUpdateStatus,
    LegacyHandoverCreate,
    LegacyHandoverListResponse,
    LegacyHandoverRead,
    LegacyHandoverUpdate,
    StudentNeedCreate,
    StudentNeedListResponse,
    StudentNeedRead,
    StudentNeedUpdate,
)
from app.services.legacy import (
    acknowledge_handover,
    create_handover,
    submit_handover,
    update_handover,
)
from app.services.matching import run_matching_for_need

logger = logging.getLogger(__name__)

router = APIRouter(tags=["phase7"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_student_profile(db: Session, user_id: str, institution_id: str) -> StudentProfile:
    """Return the student profile for this user+institution, or raise 404."""
    profile = (
        db.query(StudentProfile)
        .filter(
            StudentProfile.user_id == user_id,
            StudentProfile.institution_id == institution_id,
        )
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No student profile found for your account in this institution. "
                "Create a student profile first."
            ),
        )
    return profile


def _enrich_match(match: HelperMatch) -> HelperMatchRead:
    offer = match.help_offer
    owner = getattr(offer, "user", None) if offer else None
    return HelperMatchRead.model_validate(
        {
            **{col.key: getattr(match, col.key) for col in match.__table__.columns},
            "offer_title": offer.title if offer else None,
            "offer_category": offer.category if offer else None,
            "offer_delivery_mode": offer.delivery_mode if offer else None,
            "offer_owner_name": owner.full_name if owner else None,
        }
    )


def _enrich_handover(h: LegacyHandover) -> LegacyHandoverRead:
    position = getattr(h, "position", None)
    outgoing = getattr(h, "outgoing_user", None)
    incoming = getattr(h, "incoming_user", None)
    return LegacyHandoverRead.model_validate(
        {
            **{col.key: getattr(h, col.key) for col in h.__table__.columns},
            "position_title": position.title if position else None,
            "outgoing_user_name": outgoing.full_name if outgoing else None,
            "incoming_user_name": incoming.full_name if incoming else None,
        }
    )


def _enrich_memory(m: EventMemory) -> EventMemoryRead:
    author = getattr(m, "author", None)
    opp = getattr(m, "opportunity", None)
    raw_media = getattr(m, "media_assets", []) or []
    media_list = raw_media if isinstance(raw_media, (list, tuple)) else [raw_media]
    from app.services.media_service import to_media_asset_read

    return EventMemoryRead.model_validate(
        {
            **{col.key: getattr(m, col.key) for col in m.__table__.columns},
            "author_name": author.full_name if author else None,
            "opportunity_title": opp.title if opp else None,
            "media_assets": [to_media_asset_read(a) for a in media_list],
        }
    )


def _enrich_task(t: FollowUpTask) -> FollowUpTaskRead:
    assignee = getattr(t, "assignee", None)
    creator = getattr(t, "creator", None)
    return FollowUpTaskRead.model_validate(
        {
            **{col.key: getattr(t, col.key) for col in t.__table__.columns},
            "assignee_name": assignee.full_name if assignee else None,
            "creator_name": creator.full_name if creator else None,
        }
    )


# ---------------------------------------------------------------------------
# Student Needs
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/needs",
    response_model=StudentNeedRead,
    status_code=status.HTTP_201_CREATED,
    summary="Declare a new student need",
)
def create_need(
    institution_id: str,
    payload: StudentNeedCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> StudentNeedRead:
    profile = _get_student_profile(db, current_user.id, institution_id)
    need = StudentNeed(
        student_profile_id=profile.id,
        institution_id=institution_id,
        title=payload.title,
        category=payload.category,
        description=payload.description,
        preferred_delivery_mode=payload.preferred_delivery_mode,
        urgency=payload.urgency,
        status=NeedStatus.OPEN,
        extra_data=payload.extra_data,
    )
    db.add(need)
    db.commit()
    db.refresh(need)
    return StudentNeedRead.model_validate(need)


@router.get(
    "/institutions/{institution_id}/needs",
    response_model=StudentNeedListResponse,
    summary="List student needs for the current user in this institution",
)
def list_needs(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> StudentNeedListResponse:
    profile = _get_student_profile(db, current_user.id, institution_id)
    q = db.query(StudentNeed).filter(StudentNeed.student_profile_id == profile.id)
    if status_filter:
        q = q.filter(StudentNeed.status == status_filter)
    total = q.count()
    items = q.order_by(StudentNeed.created_at.desc()).offset(offset).limit(limit).all()
    return StudentNeedListResponse(
        items=[StudentNeedRead.model_validate(n) for n in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/institutions/{institution_id}/needs/{need_id}",
    response_model=StudentNeedRead,
    summary="Get a specific student need",
)
def get_need(
    institution_id: str,
    need_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> StudentNeedRead:
    profile = _get_student_profile(db, current_user.id, institution_id)
    need = (
        db.query(StudentNeed)
        .filter(
            StudentNeed.id == need_id,
            StudentNeed.student_profile_id == profile.id,
        )
        .first()
    )
    if not need:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found")
    return StudentNeedRead.model_validate(need)


@router.patch(
    "/institutions/{institution_id}/needs/{need_id}",
    response_model=StudentNeedRead,
    summary="Update a student need",
)
def update_need(
    institution_id: str,
    need_id: str,
    payload: StudentNeedUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> StudentNeedRead:
    profile = _get_student_profile(db, current_user.id, institution_id)
    need = (
        db.query(StudentNeed)
        .filter(
            StudentNeed.id == need_id,
            StudentNeed.student_profile_id == profile.id,
        )
        .first()
    )
    if not need:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found")

    if payload.status and payload.status not in (
        NeedStatus.RESOLVED.value,
        NeedStatus.WITHDRAWN.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only 'resolved' or 'withdrawn' status transitions are allowed via PATCH.",
        )

    update_fields = payload.model_dump(exclude_unset=True)
    for k, v in update_fields.items():
        setattr(need, k, v)
    need.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(need)
    return StudentNeedRead.model_validate(need)


@router.post(
    "/institutions/{institution_id}/needs/{need_id}/run-matching",
    response_model=HelperMatchListResponse,
    summary="Run the matching engine for an OPEN need",
)
def run_matching(
    institution_id: str,
    need_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    replace_existing: bool = Query(default=False),
) -> HelperMatchListResponse:
    profile = _get_student_profile(db, current_user.id, institution_id)
    need = (
        db.query(StudentNeed)
        .filter(
            StudentNeed.id == need_id,
            StudentNeed.student_profile_id == profile.id,
        )
        .first()
    )
    if not need:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found")

    try:
        new_matches = run_matching_for_need(db, need, replace_existing=replace_existing)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    db.commit()
    for m in new_matches:
        db.refresh(m)

    return HelperMatchListResponse(
        items=[_enrich_match(m) for m in new_matches],
        total=len(new_matches),
        limit=len(new_matches),
        offset=0,
    )


# ---------------------------------------------------------------------------
# Helper Matches
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/needs/{need_id}/matches",
    response_model=HelperMatchListResponse,
    summary="List all matches for a student need",
)
def list_matches_for_need(
    institution_id: str,
    need_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    match_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HelperMatchListResponse:
    profile = _get_student_profile(db, current_user.id, institution_id)
    need = (
        db.query(StudentNeed)
        .filter(
            StudentNeed.id == need_id,
            StudentNeed.student_profile_id == profile.id,
        )
        .first()
    )
    if not need:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found")

    q = db.query(HelperMatch).filter(HelperMatch.need_id == need_id)
    if match_status:
        q = q.filter(HelperMatch.status == match_status)
    total = q.count()
    items = q.order_by(HelperMatch.score.desc()).offset(offset).limit(limit).all()

    # Mark all as seen
    for m in items:
        if not m.is_seen:
            m.is_seen = True
    db.commit()

    return HelperMatchListResponse(
        items=[_enrich_match(m) for m in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/institutions/{institution_id}/matches/{match_id}",
    response_model=HelperMatchRead,
    summary="Get a specific helper match",
)
def get_match(
    institution_id: str,
    match_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> HelperMatchRead:
    match = (
        db.query(HelperMatch)
        .filter(
            HelperMatch.id == match_id,
            HelperMatch.institution_id == institution_id,
        )
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return _enrich_match(match)


@router.patch(
    "/institutions/{institution_id}/matches/{match_id}/status",
    response_model=HelperMatchRead,
    summary="Accept or dismiss a helper match",
)
def update_match_status(
    institution_id: str,
    match_id: str,
    payload: HelperMatchUpdateStatus,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> HelperMatchRead:
    if payload.status not in (MatchStatus.ACCEPTED.value, MatchStatus.DISMISSED.value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status must be 'accepted' or 'dismissed'.",
        )
    match = (
        db.query(HelperMatch)
        .filter(
            HelperMatch.id == match_id,
            HelperMatch.institution_id == institution_id,
        )
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.status != MatchStatus.PROPOSED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only PROPOSED matches can be updated; current status: '{match.status}'.",
        )
    match.status = MatchStatus(payload.status)
    match.is_seen = True
    match.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(match)
    return _enrich_match(match)


# ---------------------------------------------------------------------------
# Legacy Handovers
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/handovers",
    response_model=LegacyHandoverRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a DRAFT legacy handover",
)
def create_handover_endpoint(
    institution_id: str,
    payload: LegacyHandoverCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> LegacyHandoverRead:
    handover = create_handover(
        db,
        institution_id=institution_id,
        outgoing_user_id=current_user.id,
        title=payload.title,
        position_id=payload.position_id,
        incoming_user_id=payload.incoming_user_id,
        accomplishments_summary=payload.accomplishments_summary,
        ongoing_work=payload.ongoing_work,
        key_contacts=[c.model_dump() for c in payload.key_contacts],
        lessons_learned=payload.lessons_learned,
        recommended_first_steps=payload.recommended_first_steps,
    )
    db.commit()
    db.refresh(handover)
    return _enrich_handover(handover)


@router.get(
    "/institutions/{institution_id}/handovers",
    response_model=LegacyHandoverListResponse,
    summary="List handovers visible to the current user in this institution",
)
def list_handovers(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    handover_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LegacyHandoverListResponse:
    q = db.query(LegacyHandover).filter(
        LegacyHandover.institution_id == institution_id,
        (LegacyHandover.outgoing_user_id == current_user.id)
        | (LegacyHandover.incoming_user_id == current_user.id),
    )
    if handover_status:
        q = q.filter(LegacyHandover.status == handover_status)
    total = q.count()
    items = q.order_by(LegacyHandover.updated_at.desc()).offset(offset).limit(limit).all()
    return LegacyHandoverListResponse(
        items=[_enrich_handover(h) for h in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/institutions/{institution_id}/handovers/{handover_id}",
    response_model=LegacyHandoverRead,
    summary="Get a specific handover",
)
def get_handover_endpoint(
    institution_id: str,
    handover_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> LegacyHandoverRead:
    h = (
        db.query(LegacyHandover)
        .filter(
            LegacyHandover.id == handover_id,
            LegacyHandover.institution_id == institution_id,
        )
        .first()
    )
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handover not found")
    return _enrich_handover(h)


@router.patch(
    "/institutions/{institution_id}/handovers/{handover_id}",
    response_model=LegacyHandoverRead,
    summary="Update a DRAFT handover",
)
def update_handover_endpoint(
    institution_id: str,
    handover_id: str,
    payload: LegacyHandoverUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> LegacyHandoverRead:
    h = (
        db.query(LegacyHandover)
        .filter(
            LegacyHandover.id == handover_id,
            LegacyHandover.institution_id == institution_id,
        )
        .first()
    )
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handover not found")

    update_fields = payload.model_dump(exclude_unset=True)
    if "key_contacts" in update_fields and update_fields["key_contacts"] is not None:
        update_fields["key_contacts"] = [
            c.model_dump() if hasattr(c, "model_dump") else c for c in update_fields["key_contacts"]
        ]

    try:
        h = update_handover(db, h, requesting_user_id=current_user.id, **update_fields)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    db.commit()
    db.refresh(h)
    return _enrich_handover(h)


@router.post(
    "/institutions/{institution_id}/handovers/{handover_id}/submit",
    response_model=LegacyHandoverRead,
    summary="Submit a DRAFT handover for review by the incoming holder",
)
def submit_handover_endpoint(
    institution_id: str,
    handover_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> LegacyHandoverRead:
    h = (
        db.query(LegacyHandover)
        .filter(
            LegacyHandover.id == handover_id,
            LegacyHandover.institution_id == institution_id,
        )
        .first()
    )
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handover not found")
    try:
        h = submit_handover(db, h, requesting_user_id=current_user.id)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    db.commit()
    db.refresh(h)
    return _enrich_handover(h)


@router.post(
    "/institutions/{institution_id}/handovers/{handover_id}/acknowledge",
    response_model=LegacyHandoverRead,
    summary="Incoming holder acknowledges receipt of a SUBMITTED handover",
)
def acknowledge_handover_endpoint(
    institution_id: str,
    handover_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> LegacyHandoverRead:
    h = (
        db.query(LegacyHandover)
        .filter(
            LegacyHandover.id == handover_id,
            LegacyHandover.institution_id == institution_id,
        )
        .first()
    )
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handover not found")
    try:
        h = acknowledge_handover(db, h, requesting_user_id=current_user.id)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    db.commit()
    db.refresh(h)
    return _enrich_handover(h)


# ---------------------------------------------------------------------------
# Event Memories
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/memories",
    response_model=EventMemoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an institutional event memory record",
)
def create_memory(
    institution_id: str,
    payload: EventMemoryCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> EventMemoryRead:
    memory = EventMemory(
        institution_id=institution_id,
        opportunity_id=payload.opportunity_id,
        handover_id=payload.handover_id,
        author_user_id=current_user.id,
        title=payload.title,
        what_worked=payload.what_worked,
        what_did_not_work=payload.what_did_not_work,
        attendance_notes=payload.attendance_notes,
        outcome_summary=payload.outcome_summary,
        context_notes=payload.context_notes,
        tags=payload.tags,
        is_current=True,
        extra_data=payload.extra_data,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return _enrich_memory(memory)


@router.get(
    "/institutions/{institution_id}/memories",
    response_model=EventMemoryListResponse,
    summary="List current event memory records for this institution",
)
def list_memories(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    opportunity_id: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    current_only: bool = Query(default=True),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> EventMemoryListResponse:
    q = db.query(EventMemory).filter(EventMemory.institution_id == institution_id)
    if current_only:
        q = q.filter(EventMemory.is_current.is_(True))
    if opportunity_id:
        q = q.filter(EventMemory.opportunity_id == opportunity_id)
    total = q.count()
    items = q.order_by(EventMemory.created_at.desc()).offset(offset).limit(limit).all()

    result = [_enrich_memory(m) for m in items]
    if tag:
        result = [r for r in result if tag.lower() in [t.lower() for t in r.tags]]

    return EventMemoryListResponse(
        items=result,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/institutions/{institution_id}/memories/{memory_id}",
    response_model=EventMemoryRead,
    summary="Get a specific event memory record",
)
def get_memory(
    institution_id: str,
    memory_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> EventMemoryRead:
    m = (
        db.query(EventMemory)
        .filter(
            EventMemory.id == memory_id,
            EventMemory.institution_id == institution_id,
        )
        .first()
    )
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory record not found")
    return _enrich_memory(m)


# ---------------------------------------------------------------------------
# Follow-Up Tasks
# ---------------------------------------------------------------------------


@router.post(
    "/institutions/{institution_id}/tasks",
    response_model=FollowUpTaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a follow-up task",
)
def create_task(
    institution_id: str,
    payload: FollowUpTaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> FollowUpTaskRead:
    source = TaskSource.MANUAL
    if payload.handover_id and not payload.match_id:
        source = TaskSource.HANDOVER
    elif payload.match_id and not payload.handover_id:
        source = TaskSource.MATCH

    task = FollowUpTask(
        institution_id=institution_id,
        source=source,
        handover_id=payload.handover_id,
        match_id=payload.match_id,
        title=payload.title,
        description=payload.description,
        assignee_user_id=payload.assignee_user_id,
        creator_user_id=current_user.id,
        due_date=payload.due_date,
        priority=payload.priority,
        extra_data=payload.extra_data,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _enrich_task(task)


@router.get(
    "/institutions/{institution_id}/tasks",
    response_model=FollowUpTaskListResponse,
    summary="List tasks assigned to or created by the current user",
)
def list_tasks(
    institution_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
    completed: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FollowUpTaskListResponse:
    q = db.query(FollowUpTask).filter(
        FollowUpTask.institution_id == institution_id,
        (FollowUpTask.assignee_user_id == current_user.id)
        | (FollowUpTask.creator_user_id == current_user.id),
    )
    if completed is not None:
        q = q.filter(FollowUpTask.is_completed.is_(completed))
    total = q.count()
    items = q.order_by(FollowUpTask.created_at.desc()).offset(offset).limit(limit).all()
    return FollowUpTaskListResponse(
        items=[_enrich_task(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/institutions/{institution_id}/tasks/{task_id}",
    response_model=FollowUpTaskRead,
    summary="Get a specific follow-up task",
)
def get_task(
    institution_id: str,
    task_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> FollowUpTaskRead:
    t = (
        db.query(FollowUpTask)
        .filter(
            FollowUpTask.id == task_id,
            FollowUpTask.institution_id == institution_id,
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _enrich_task(t)


@router.patch(
    "/institutions/{institution_id}/tasks/{task_id}",
    response_model=FollowUpTaskRead,
    summary="Update a follow-up task",
)
def update_task(
    institution_id: str,
    task_id: str,
    payload: FollowUpTaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_institution_membership)],
) -> FollowUpTaskRead:
    t = (
        db.query(FollowUpTask)
        .filter(
            FollowUpTask.id == task_id,
            FollowUpTask.institution_id == institution_id,
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.is_completed is not None and t.assignee_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assignee may mark a task as completed.",
        )

    update_fields = payload.model_dump(exclude_unset=True)
    for k, v in update_fields.items():
        setattr(t, k, v)
    if payload.is_completed is True and not t.completed_at:
        t.completed_at = datetime.now(UTC)
    t.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(t)
    return _enrich_task(t)
