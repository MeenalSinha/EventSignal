"""User model: platform account, credentials, and global permissions.

Migration note: introduced in Alembic revision 0004.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.campus_position import CampusRoleAssignment
    from app.models.membership import InstitutionMembership


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # Unique email address used for login and notifications
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Cryptographically hashed password (PBKDF2-HMAC-SHA256)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Real or verified full name
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Whether the user can authenticate
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Global platform administrator (can manage all institutions)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Extensible metadata (e.g. phone, bio, avatar)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    memberships: Mapped[list[InstitutionMembership]] = relationship(
        back_populates="user",
        foreign_keys="[InstitutionMembership.user_id]",
        cascade="all, delete-orphan",
    )
    role_assignments: Mapped[list[CampusRoleAssignment]] = relationship(
        back_populates="user",
        foreign_keys="[CampusRoleAssignment.user_id]",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="actor",
        foreign_keys="[AuditLog.actor_user_id]",
    )
