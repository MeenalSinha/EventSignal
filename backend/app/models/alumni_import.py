"""Alumni batch import audit and job models for EventSignal Phase 8.

Enables verified college administrators to import alumni directories via CSV
with dry-run validation, duplicate detection, and explicit consent handling.

CRITICAL PRIVACY GUARANTEE:
Imported identities NEVER automatically acquire public discoverability or
`willing_to_connect` mentorship consent.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_id


class ImportJobStatus(enum.StrEnum):
    """Execution status of an institutional import job."""

    PREVIEW = "preview"
    """Dry-run validation completed; pending administrator review."""

    COMMITTED = "committed"
    """Administrator confirmed and records were persisted."""

    FAILED = "failed"
    """Validation or file structure failed critically."""


class AlumniImportJob(TimestampMixin, Base):
    """Institutional audit log of batch alumni CSV imports."""

    __tablename__ = "alumni_import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uploader_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[ImportJobStatus] = mapped_column(
        Enum(ImportJobStatus, name="import_job_status"),
        default=ImportJobStatus.PREVIEW,
        nullable=False,
    )

    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Detailed row-by-row validation feedback and warnings
    validation_errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    __table_args__ = (Index("ix_alumni_import_inst_status", "institution_id", "status"),)
