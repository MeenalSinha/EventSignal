"""Read-only opportunity listing.

Phase 2 note: This route replaces GET /api/v1/events from Phase 1.
The endpoint URL is now /opportunities. The /events URL is intentionally
not preserved as an alias to avoid confusion.

Phase 2 has no submission endpoint. This route exists so the frontend's
empty state is derived from the actual database rather than assumed.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_session
from app.models import Opportunity
from app.schemas.opportunity import OpportunityList, OpportunityRead

router = APIRouter(tags=["opportunities"])

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@router.get("/opportunities", response_model=OpportunityList, summary="List stored opportunities")
@router.get(
    "/events",
    response_model=OpportunityList,
    summary="List stored opportunities (compatibility endpoint)",
)
def list_opportunities(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OpportunityList:
    total = session.scalar(select(func.count()).select_from(Opportunity)) or 0
    rows = session.scalars(
        select(Opportunity)
        .options(selectinload(Opportunity.sources))
        .order_by(Opportunity.created_at.desc(), Opportunity.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return OpportunityList(
        items=[OpportunityRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
