"""Pydantic schemas for audit logs and security events."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Immutable audit trail record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str | None
    actor_user_id: str | None
    action: str
    target_type: str
    target_id: str
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime
