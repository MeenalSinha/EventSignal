"""Audit logging service for security tracking and compliance."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    session: Session,
    action: str,
    target_type: str,
    target_id: str,
    actor_user_id: str | None = None,
    institution_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record an immutable security event."""
    log = AuditLog(
        action=action,
        target_type=target_type,
        target_id=target_id,
        actor_user_id=actor_user_id,
        institution_id=institution_id,
        details=details or {},
        ip_address=ip_address,
    )
    session.add(log)
    session.flush()
    return log
