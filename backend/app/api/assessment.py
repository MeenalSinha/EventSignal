"""Phase 4: Opportunity assessment endpoints.

Routes:
  POST  /api/v1/opportunities/{opportunity_id}/assess
        Trigger (or re-trigger) assessment for a single opportunity.
        Returns the full AssessmentRead.

  GET   /api/v1/opportunities/{opportunity_id}/assessment
        Return the latest persisted assessment (404 if none yet).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_session
from app.models.opportunity import Opportunity
from app.models.opportunity_assessment import OpportunityAssessment
from app.schemas.assessment import OpportunityAssessmentRead
from app.services.assessment import assess_opportunity

router = APIRouter(tags=["assessment"])


@router.post(
    "/opportunities/{opportunity_id}/assess",
    response_model=OpportunityAssessmentRead,
    status_code=status.HTTP_200_OK,
    summary="Run (or re-run) assessment for an opportunity",
    description=(
        "Evaluates completeness, evidence quality, and consistency for the given "
        "opportunity using its persisted FieldEvidence records. "
        "Re-running replaces the previous assessment. No network calls are made."
    ),
)
def run_assessment(
    opportunity_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> OpportunityAssessmentRead:
    try:
        record = assess_opportunity(opportunity_id=opportunity_id, session=session)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return OpportunityAssessmentRead.model_validate(record)


@router.get(
    "/opportunities/{opportunity_id}/assessment",
    response_model=OpportunityAssessmentRead,
    summary="Retrieve the latest assessment for an opportunity",
    description=(
        "Returns the persisted assessment for the given opportunity. "
        "Returns 404 if assessment has not been run yet. "
        "Call POST /assess first to generate one."
    ),
)
def get_assessment(
    opportunity_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> OpportunityAssessmentRead:
    # Verify opportunity exists
    opp_exists = session.scalars(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    ).first()
    if opp_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id!r} not found",
        )

    record = session.scalars(
        select(OpportunityAssessment).where(
            OpportunityAssessment.opportunity_id == opportunity_id
        )
    ).first()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No assessment found for opportunity {opportunity_id!r}. "
                "POST /assess to generate one."
            ),
        )

    return OpportunityAssessmentRead.model_validate(record)
