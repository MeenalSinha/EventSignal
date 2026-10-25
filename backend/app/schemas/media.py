"""Pydantic schemas for Cloudinary media uploads and asset associations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UploadSignatureRequest(BaseModel):
    """Input payload to request a secure server-signed upload authorization."""

    media_purpose: str = Field(default="opportunity_poster", max_length=64)
    institution_id: str | None = Field(default=None, max_length=36)
    opportunity_id: str | None = Field(default=None, max_length=36)
    event_memory_id: str | None = Field(default=None, max_length=36)
    legacy_handover_id: str | None = Field(default=None, max_length=36)


class UploadSignatureResponse(BaseModel):
    """Signed upload parameters returned to the authenticated client."""

    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    upload_url: str
    allowed_formats: list[str]
    max_file_size_bytes: int
    tags: str


class CompleteUploadRequest(BaseModel):
    """Payload submitted after client uploads to Cloudinary to verify and associate the asset."""

    cloudinary_public_id: str = Field(min_length=1, max_length=255)
    secure_url: str = Field(min_length=1, max_length=1024)
    resource_type: str = Field(default="image", max_length=32)
    format: str | None = Field(default=None, max_length=16)
    bytes: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    alt_text: str | None = Field(default=None, max_length=255)
    caption: str | None = None
    media_purpose: str = Field(default="opportunity_poster", max_length=64)
    institution_id: str | None = Field(default=None, max_length=36)
    opportunity_id: str | None = Field(default=None, max_length=36)
    event_memory_id: str | None = Field(default=None, max_length=36)
    legacy_handover_id: str | None = Field(default=None, max_length=36)
    signature: str | None = None
    version: int | None = None


class MediaAssetRead(BaseModel):
    """Public read contract for a verified media asset."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    cloudinary_public_id: str
    secure_url: str
    thumbnail_url: str | None = None
    card_url: str | None = None
    resource_type: str
    format: str | None
    bytes: int | None
    width: int | None
    height: int | None
    alt_text: str | None
    caption: str | None
    media_purpose: str
    institution_id: str | None
    uploader_user_id: str
    opportunity_id: str | None = None
    event_memory_id: str | None = None
    legacy_handover_id: str | None = None
    is_verified: bool
    created_at: datetime
    extra_data: dict[str, Any] | None = None


class MediaStatusResponse(BaseModel):
    """Configuration and feature-flag status for Cloudinary media handling."""

    enabled: bool
    cloud_name: str | None = None
    allowed_formats: list[str]
    max_file_size_bytes: int
    folder_prefix: str
