"""API endpoints for HelpOffer publishing, discovery, filtering, and connection requests."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.connection import ConnectionRequestRead, HelpOfferRequestCreate
from app.schemas.help_offer import (
    HelpOfferCreate,
    HelpOfferListResponse,
    HelpOfferRead,
    HelpOfferUpdate,
)
from app.services import help_offer as offer_service

router = APIRouter(prefix="/institutions/{institution_id}/help-offers", tags=["help-offers"])


@router.get("", response_model=HelpOfferListResponse)
def discover_help_offers(
    institution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    category: str | None = None,
    search: str | None = None,
    delivery_mode: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> HelpOfferListResponse:
    """Discover active help offers within the authorized institution community."""
    return offer_service.discover_help_offers(
        db,
        institution_id=institution_id,
        current_user=current_user,
        category=category,
        search=search,
        delivery_mode=delivery_mode,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=HelpOfferRead, status_code=status.HTTP_201_CREATED)
def create_help_offer(
    institution_id: str,
    data: HelpOfferCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HelpOfferRead:
    """Create and publish a new help offer."""
    offer = offer_service.create_help_offer(db, current_user.id, institution_id, data)
    db.commit()
    return offer


@router.get("/mine", response_model=list[HelpOfferRead])
def list_my_help_offers(
    institution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[HelpOfferRead]:
    """Retrieve all help offers published by the authenticated user in this workspace."""
    return offer_service.list_my_help_offers(db, current_user.id, institution_id)


@router.get("/{offer_id}", response_model=HelpOfferRead)
def get_help_offer(
    institution_id: str,
    offer_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HelpOfferRead:
    """Retrieve details of a specific help offer."""
    return offer_service.get_help_offer(db, offer_id, current_user)


@router.patch("/{offer_id}", response_model=HelpOfferRead)
def update_help_offer(
    institution_id: str,
    offer_id: str,
    data: HelpOfferUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HelpOfferRead:
    """Update an offer's details, pause/resume status, or willingness to help."""
    updated = offer_service.update_help_offer(db, offer_id, current_user.id, data)
    db.commit()
    return updated


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_help_offer(
    institution_id: str,
    offer_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Archive a help offer (removes it from active discovery)."""
    offer_service.archive_help_offer(db, offer_id, current_user.id)
    db.commit()


@router.post(
    "/{offer_id}/requests",
    response_model=ConnectionRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_offer_request(
    institution_id: str,
    offer_id: str,
    data: HelpOfferRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConnectionRequestRead:
    """Submit a purpose-specific help request on an active published offer."""
    req = offer_service.create_help_offer_request(db, offer_id, current_user, data)
    db.commit()
    db.refresh(req)
    return ConnectionRequestRead.model_validate(req)


@router.get("/{offer_id}/requests", response_model=list[ConnectionRequestRead])
def list_offer_requests(
    institution_id: str,
    offer_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ConnectionRequestRead]:
    """List incoming requests on a help offer (accessible to offer owner or admin)."""
    requests = offer_service.list_offer_requests(db, offer_id, current_user)
    return [ConnectionRequestRead.model_validate(r) for r in requests]
