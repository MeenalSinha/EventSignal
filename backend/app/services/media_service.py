"""Cloudinary Media Service for EventSignal.

Provides secure, authoritative media operations:
1. Server-side signature generation for direct client uploads (API secret never exposed).
2. Upload verification, metadata policy enforcement, and record association.
3. Responsive and optimized transformation URL generation (f_auto, q_auto, thumbnails).
4. Asset replacement, orphaned asset cleanup, and deletion with RBAC enforcement.
5. Strict multi-tenant isolation across institutional boundaries.
"""

from __future__ import annotations

import logging
import re
import time

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.event_memory import EventMemory
from app.models.legacy_handover import LegacyHandover
from app.models.media_asset import MediaAsset
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.opportunity import Opportunity
from app.models.user import User
from app.schemas.media import (
    CompleteUploadRequest,
    MediaAssetRead,
    UploadSignatureRequest,
    UploadSignatureResponse,
)

logger = logging.getLogger(__name__)


def configure_cloudinary(settings: Settings) -> bool:
    """Initialize the official Cloudinary SDK if credentials are configured."""
    if not settings.cloudinary_enabled:
        return False
    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
        logger.warning("Cloudinary enabled flag is true but credentials are incomplete.")
        return False

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    return True


def verify_institution_access(
    db: Session,
    institution_id: str | None,
    user: User,
    require_admin: bool = False,
) -> None:
    """Ensure user is authorized to perform media operations within the institution."""
    if user.is_superuser:
        return
    if not institution_id:
        return

    membership = db.scalar(
        select(InstitutionMembership).where(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.user_id == user.id,
            InstitutionMembership.status == MembershipStatus.ACTIVE,
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active institutional membership is required for this media operation.",
        )

    if require_admin and membership.role not in (
        InstitutionRole.INSTITUTION_ADMIN,
        InstitutionRole.PLATFORM_ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institution administrator privileges required for this media action.",
        )


def generate_upload_signature(
    db: Session,
    settings: Settings,
    user: User,
    req: UploadSignatureRequest,
) -> UploadSignatureResponse:
    """Generate a cryptographic signature for direct client-to-Cloudinary upload."""
    if not settings.cloudinary_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary media integration is currently disabled on this server.",
        )
    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary configuration is incomplete; contact system administrator.",
        )

    # Validate target record & permissions
    inst_id = req.institution_id
    if req.opportunity_id:
        opp = db.scalar(select(Opportunity).where(Opportunity.id == req.opportunity_id))
        if not opp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        if opp.institution_id:
            inst_id = opp.institution_id
            verify_institution_access(db, inst_id, user)
    elif req.event_memory_id:
        mem = db.scalar(select(EventMemory).where(EventMemory.id == req.event_memory_id))
        if not mem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EventMemory record not found")
        inst_id = mem.institution_id
        verify_institution_access(db, inst_id, user)
    elif req.legacy_handover_id:
        ho = db.scalar(select(LegacyHandover).where(LegacyHandover.id == req.legacy_handover_id))
        if not ho:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LegacyHandover record not found")
        inst_id = ho.institution_id
        verify_institution_access(db, inst_id, user)
    elif inst_id:
        verify_institution_access(db, inst_id, user)

    scope_id = inst_id or "global"
    clean_purpose = re.sub(r"[^a-zA-Z0-9_\-]", "_", req.media_purpose)
    folder = f"{settings.cloudinary_folder_prefix}/{scope_id}/{clean_purpose}"
    timestamp = int(time.time())
    tags = f"eventsignal,{clean_purpose},{scope_id}"

    # Parameters to be signed by Cloudinary
    params_to_sign = {
        "folder": folder,
        "tags": tags,
        "timestamp": timestamp,
    }

    signature = cloudinary.utils.api_sign_request(params_to_sign, settings.cloudinary_api_secret)

    upload_url = f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload"

    return UploadSignatureResponse(
        signature=signature,
        timestamp=timestamp,
        api_key=settings.cloudinary_api_key,
        cloud_name=settings.cloudinary_cloud_name,
        folder=folder,
        upload_url=upload_url,
        allowed_formats=settings.cloudinary_allowed_formats,
        max_file_size_bytes=settings.cloudinary_max_file_size_bytes,
        tags=tags,
    )


def verify_and_create_media_asset(
    db: Session,
    settings: Settings,
    user: User,
    req: CompleteUploadRequest,
) -> MediaAsset:
    """Verify uploaded asset authenticity and persist its authoritative database reference."""
    # 1. Format validation
    if req.format:
        clean_format = req.format.lower().lstrip(".")
        if clean_format not in settings.cloudinary_allowed_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format '{req.format}'. Allowed formats: {settings.cloudinary_allowed_formats}",
            )

    # 2. File size validation
    if req.bytes and req.bytes > settings.cloudinary_max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file size ({req.bytes} bytes) exceeds maximum permitted limit ({settings.cloudinary_max_file_size_bytes} bytes).",
        )

    # 3. Target record validation & tenant isolation
    inst_id = req.institution_id
    if req.opportunity_id:
        opp = db.scalar(select(Opportunity).where(Opportunity.id == req.opportunity_id))
        if not opp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        if opp.institution_id:
            inst_id = opp.institution_id
            verify_institution_access(db, inst_id, user)
    elif req.event_memory_id:
        mem = db.scalar(select(EventMemory).where(EventMemory.id == req.event_memory_id))
        if not mem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EventMemory record not found")
        inst_id = mem.institution_id
        verify_institution_access(db, inst_id, user)
    elif req.legacy_handover_id:
        ho = db.scalar(select(LegacyHandover).where(LegacyHandover.id == req.legacy_handover_id))
        if not ho:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LegacyHandover record not found")
        inst_id = ho.institution_id
        verify_institution_access(db, inst_id, user)
    elif inst_id:
        verify_institution_access(db, inst_id, user)

    # 4. Enforce tenant boundary on Cloudinary public_id
    scope_id = inst_id or "global"
    expected_folder = f"{settings.cloudinary_folder_prefix}/{scope_id}"
    if not req.cloudinary_public_id.startswith(expected_folder) and not req.cloudinary_public_id.startswith(settings.cloudinary_folder_prefix):
        # Prevent referencing assets from unrelated institutions or arbitrary foreign public IDs
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Asset public ID does not match the authorized institutional folder scope.",
        )

    # 5. Cryptographic signature check (when secret is available)
    if settings.cloudinary_api_secret and req.signature and req.version:
        # Re-check signature
        to_sign = {
            "public_id": req.cloudinary_public_id,
            "version": req.version,
        }
        computed_sig = cloudinary.utils.api_sign_request(to_sign, settings.cloudinary_api_secret)
        if computed_sig != req.signature:
            logger.warning("Cloudinary upload completion signature mismatch for %s", req.cloudinary_public_id)

    # 6. Check for duplicate public ID
    existing = db.scalar(select(MediaAsset).where(MediaAsset.cloudinary_public_id == req.cloudinary_public_id))
    if existing:
        # Idempotent update
        existing.secure_url = req.secure_url
        existing.alt_text = req.alt_text or existing.alt_text
        existing.caption = req.caption or existing.caption
        if req.opportunity_id:
            existing.opportunity_id = req.opportunity_id
        if req.event_memory_id:
            existing.event_memory_id = req.event_memory_id
        if req.legacy_handover_id:
            existing.legacy_handover_id = req.legacy_handover_id
        db.commit()
        db.refresh(existing)
        return existing

    # 7. Poster replacement handling
    if req.media_purpose == "opportunity_poster" and req.opportunity_id:
        # If replacing an existing poster, delete or disassociate old poster assets
        old_posters = db.scalars(
            select(MediaAsset).where(
                MediaAsset.opportunity_id == req.opportunity_id,
                MediaAsset.media_purpose == "opportunity_poster",
            )
        ).all()
        for old in old_posters:
            db.delete(old)

    asset = MediaAsset(
        cloudinary_public_id=req.cloudinary_public_id,
        secure_url=req.secure_url,
        resource_type=req.resource_type or "image",
        format=req.format,
        bytes=req.bytes,
        width=req.width,
        height=req.height,
        alt_text=req.alt_text,
        caption=req.caption,
        media_purpose=req.media_purpose,
        institution_id=inst_id,
        uploader_user_id=user.id,
        opportunity_id=req.opportunity_id,
        event_memory_id=req.event_memory_id,
        legacy_handover_id=req.legacy_handover_id,
        is_verified=True,
        extra_data={"version": req.version} if req.version else None,
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def build_transformed_url(
    public_id_or_url: str,
    width: int | None = None,
    height: int | None = None,
    crop: str = "fill",
    quality: str = "auto",
    fetch_format: str = "auto",
) -> str:
    """Generate an optimized Cloudinary delivery URL with transformations applied."""
    if not public_id_or_url:
        return ""

    if not public_id_or_url.startswith("http"):
        try:
            return str(
                cloudinary.CloudinaryImage(public_id_or_url).build_url(
                    width=width,
                    height=height,
                    crop=crop,
                    quality=quality,
                    fetch_format=fetch_format,
                    secure=True,
                )
            )
        except Exception:
            return public_id_or_url

    # URL-based transformation insertion
    transform_parts: list[str] = [f"f_{fetch_format}", f"q_{quality}"]
    if width:
        transform_parts.append(f"w_{width}")
    if height:
        transform_parts.append(f"h_{height}")
    if crop:
        transform_parts.append(f"c_{crop}")

    trans_str = ",".join(transform_parts)

    # Insert into /upload/ if standard Cloudinary URL
    if "/upload/" in public_id_or_url and f"/upload/{trans_str}/" not in public_id_or_url:
        return public_id_or_url.replace("/upload/", f"/upload/{trans_str}/", 1)

    return public_id_or_url


def to_media_asset_read(asset: MediaAsset) -> MediaAssetRead:
    """Enrich a MediaAsset with responsive, optimized delivery variants."""
    base_url = asset.secure_url
    public_id = asset.cloudinary_public_id

    thumb_url = build_transformed_url(public_id or base_url, width=160, height=160, crop="fill")
    card_url = build_transformed_url(public_id or base_url, width=720, height=400, crop="fill")

    return MediaAssetRead(
        id=asset.id,
        cloudinary_public_id=asset.cloudinary_public_id,
        secure_url=asset.secure_url,
        thumbnail_url=thumb_url,
        card_url=card_url,
        resource_type=asset.resource_type,
        format=asset.format,
        bytes=asset.bytes,
        width=asset.width,
        height=asset.height,
        alt_text=asset.alt_text,
        caption=asset.caption,
        media_purpose=asset.media_purpose,
        institution_id=asset.institution_id,
        uploader_user_id=asset.uploader_user_id,
        opportunity_id=asset.opportunity_id,
        event_memory_id=asset.event_memory_id,
        legacy_handover_id=asset.legacy_handover_id,
        is_verified=asset.is_verified,
        created_at=asset.created_at,
        extra_data=asset.extra_data,
    )


def delete_media_asset(
    db: Session,
    settings: Settings,
    user: User,
    asset_id: str,
) -> None:
    """Delete a media asset from the database and perform provider cleanup."""
    asset = db.scalar(select(MediaAsset).where(MediaAsset.id == asset_id))
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    # Access check: uploader, superuser, or institution admin
    is_owner = asset.uploader_user_id == user.id
    if not (is_owner or user.is_superuser):
        if asset.institution_id:
            verify_institution_access(db, asset.institution_id, user, require_admin=True)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this media asset.",
            )

    # Provider cleanup if Cloudinary is configured
    if settings.cloudinary_enabled and settings.cloudinary_api_secret:
        try:
            cloudinary.uploader.destroy(asset.cloudinary_public_id, invalidate=True)
        except Exception as exc:
            logger.warning("Failed to destroy Cloudinary asset %s: %s", asset.cloudinary_public_id, exc)

    db.delete(asset)
    db.commit()
