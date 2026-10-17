"""Read-only event listing.

Phase 1 has no submission endpoint. This route exists so the frontend's empty state
is derived from the actual database rather than assumed.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_session
from app.models import Event
from app.schemas.event import EventList, EventRead

router = APIRouter(prefix="/events", tags=["events"])

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@router.get("", response_model=EventList, summary="List stored events")
def list_events(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EventList:
    total = session.scalar(select(func.count()).select_from(Event)) or 0
    rows = session.scalars(
        select(Event)
        .options(selectinload(Event.sources))
        .order_by(Event.created_at.desc(), Event.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return EventList(
        items=[EventRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
