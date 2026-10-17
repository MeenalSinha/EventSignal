"""AuditLog: security audit trails and administrative event logging.

Captures all security-critical operations (workspace creation, role assignments,
tenure verification, status alterations) with timestamps and actor attribution.

Migration note: introduced in Alembic revision 0004.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UTCDateTime, new_id, utcnow

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Scoped institution (if event pertains to an institutional workspace)
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="SET NULL"), index=True
    )

    # Actor who performed the action (None if system-level automated job)
    actor_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Standardized action identifier: e.g. "institution.create", "membership.assign_role"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Target entity classification: e.g. "institution", "membership", "position_assignment"
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Structured details of changes, reasons, or before/after state
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Client IP address if known
    ip_address: Mapped[str | None] = mapped_column(String(45))

    # Immutable creation timestamp
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    # Relationships
    institution: Mapped[Institution | None] = relationship(back_populates="audit_logs")
    actor: Mapped[User | None] = relationship(
        back_populates="audit_logs", foreign_keys=[actor_user_id]
    )
