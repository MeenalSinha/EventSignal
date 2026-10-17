"""OrganizationalUnit: configurable campus departments, centers, and cells.

Supports hierarchical academic departments (e.g. Computer Science, Electronics),
administrative offices (Training & Placement Cell, Alumni Relations Office),
and student bodies or societies.

Migration note: introduced in Alembic revision 0004.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id

if TYPE_CHECKING:
    from app.models.campus_position import CampusPositionDefinition, CampusRoleAssignment
    from app.models.institution import Institution


class OrganizationalUnit(TimestampMixin, Base):
    __tablename__ = "organizational_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Unit name: e.g. "Department of Computer Science & Engineering", "Training & Placement Cell"
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Short code or abbreviation: e.g. "CSE", "TPO", "ARO"
    code: Mapped[str | None] = mapped_column(String(50), index=True)

    # Unit classification: department, office, cell, center, club, committee
    unit_type: Mapped[str] = mapped_column(String(50), default="department", nullable=False)

    # Parent unit for nested hierarchies (e.g., a lab or cell within a department)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizational_units.id", ondelete="SET NULL"), index=True
    )

    # Unit mission, mandate, or description
    description: Mapped[str | None] = mapped_column(Text)

    # Contact email or portal link for this unit
    contact_email: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    institution: Mapped[Institution] = relationship(back_populates="units")
    parent: Mapped[OrganizationalUnit | None] = relationship(
        remote_side="[OrganizationalUnit.id]",
        backref="children",
    )
    positions: Mapped[list[CampusPositionDefinition]] = relationship(
        back_populates="unit",
        cascade="all, delete-orphan",
    )
    role_assignments: Mapped[list[CampusRoleAssignment]] = relationship(
        back_populates="unit",
    )
