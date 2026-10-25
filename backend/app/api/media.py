"""Media endpoints for Cloudinary upload authorization, verification, and asset lifecycle."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.database import get_db
from app.models.media_asset import MediaAsset
from app.models.user import User
from app.schemas.media import (
    CompleteUploadRequest,
    MediaAssetRead,
    MediaStatusResponse,
    UploadSignatureRequest,
    UploadSignatureResponse,
)
from app.services import media_service

router = APIRouter(prefix="/media", tags=["media"])
inst_router = APIRouter(prefix="/institutions/{institution_id}", tags=["media"])


# ---------------------------------------------------------------------------
# Global Media Operations
# ---------------------------------------------------------------------------


@router.get("/status", response_model=MediaStatusResponse)
def get_media_status(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MediaStatusResponse:
    """Return the configuration and feature-flag status for Cloudinary media uploads."""
    is_ready = settings.cloudinary_enabled and bool(
        settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret
    )
    return MediaStatusResponse(
        enabled=is_ready,
        cloud_name=settings.cloudinary_cloud_name if is_ready else None,
        allowed_formats=settings.cloudinary_allowed_formats,
        max_file_size_bytes=settings.cloudinary_max_file_size_bytes,
        folder_prefix=settings.cloudinary_folder_prefix,
    )


@router.post("/authorize-upload", response_model=UploadSignatureResponse)
def authorize_media_upload(
    req: UploadSignatureRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> UploadSignatureResponse:
    """Generate a cryptographic signature for direct client-to-Cloudinary upload.

    The client uses the returned signed parameters to POST directly to Cloudinary
    without ever receiving or exposing the server's private API secret.
    """
    return media_service.generate_upload_signature(db, settings, current_user, req)


@router.post("/complete-upload", response_model=MediaAssetRead, status_code=status.HTTP_201_CREATED)
def complete_media_upload(
    req: CompleteUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> MediaAssetRead:
    """Verify an uploaded Cloudinary asset and persist its authoritative database association."""
    asset = media_service.verify_and_create_media_asset(db, settings, current_user, req)
    return media_service.to_media_asset_read(asset)


@router.get("/{asset_id}", response_model=MediaAssetRead)
def get_media_asset(
    asset_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> MediaAssetRead:
    """Retrieve media asset metadata and responsive transformation delivery URLs."""
    asset = db.scalar(select(MediaAsset).where(MediaAsset.id == asset_id))
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    return media_service.to_media_asset_read(asset)


@router.delete("/{asset_id}")
def delete_media_asset(
    asset_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Delete a media asset record and remove the underlying asset from Cloudinary."""
    media_service.delete_media_asset(db, settings, current_user, asset_id)
    return {"status": "deleted", "id": asset_id}


# ---------------------------------------------------------------------------
# Record-Scoped Convenience Endpoints
# ---------------------------------------------------------------------------


@inst_router.get("/opportunities/{opportunity_id}/media", response_model=list[MediaAssetRead])
def list_opportunity_media(
    institution_id: str,
    opportunity_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> list[MediaAssetRead]:
    """List all verified media assets associated with an opportunity."""
    assets = db.scalars(
        select(MediaAsset).where(
            MediaAsset.opportunity_id == opportunity_id,
            MediaAsset.is_verified.is_(True),
        )
    ).all()
    return [media_service.to_media_asset_read(a) for a in assets]


@inst_router.delete("/opportunities/{opportunity_id}/poster")
def remove_opportunity_poster(
    institution_id: str,
    opportunity_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Remove the attached poster asset from an opportunity."""
    posters = db.scalars(
        select(MediaAsset).where(
            MediaAsset.opportunity_id == opportunity_id,
            MediaAsset.media_purpose == "opportunity_poster",
        )
    ).all()

    if not posters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No poster attached to this opportunity")

    for poster in posters:
        media_service.delete_media_asset(db, settings, current_user, poster.id)

    return {"status": "removed", "opportunity_id": opportunity_id}
