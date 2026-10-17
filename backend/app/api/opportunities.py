"""Opportunity listing and intake endpoints.

Phase 3: Adds POST /api/v1/opportunities/ingest for real URL submission, safe
web retrieval, generic multi-stage extraction, and evidence persistence.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.database import get_session
from app.models import Opportunity
from app.schemas.ingest import OpportunityIngestRequest, OpportunityIngestResponse
from app.schemas.opportunity import OpportunityList, OpportunityRead
from app.services.ingestion import ingest_opportunity_url
from app.services.retrieval import RetrievalError

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
    institution_id: Annotated[str | None, Query()] = None,
) -> OpportunityList:
    count_stmt = select(func.count()).select_from(Opportunity)
    query_stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.sources), selectinload(Opportunity.evidence))
        .order_by(Opportunity.created_at.desc(), Opportunity.id)
        .limit(limit)
        .offset(offset)
    )
    if institution_id:
        count_stmt = count_stmt.where(Opportunity.institution_id == institution_id)
        query_stmt = query_stmt.where(Opportunity.institution_id == institution_id)

    total = session.scalar(count_stmt) or 0
    rows = session.scalars(query_stmt).all()
    return OpportunityList(
        items=[OpportunityRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/opportunities/ingest",
    response_model=OpportunityIngestResponse,
    summary="Ingest and extract a public opportunity URL",
)
def ingest_opportunity(
    payload: OpportunityIngestRequest,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> OpportunityIngestResponse:
    settings = get_settings()
    try:
        result = ingest_opportunity_url(
            url=payload.url,
            session=session,
            settings=settings,
            force_refresh=payload.force_refresh,
            opportunity_id=payload.opportunity_id,
        )
        response.status_code = (
            status.HTTP_200_OK if result.is_duplicate else status.HTTP_201_CREATED
        )
        return result
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RetrievalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/opportunities/{opportunity_id}/sources",
    response_model=OpportunityIngestResponse,
    summary="Attach an additional public source URL to an existing opportunity",
)
def add_opportunity_source(
    opportunity_id: str,
    payload: OpportunityIngestRequest,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> OpportunityIngestResponse:
    settings = get_settings()
    try:
        result = ingest_opportunity_url(
            url=payload.url,
            session=session,
            settings=settings,
            force_refresh=payload.force_refresh,
            opportunity_id=opportunity_id,
        )
        response.status_code = (
            status.HTTP_200_OK if result.is_duplicate else status.HTTP_201_CREATED
        )
        return result
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RetrievalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
