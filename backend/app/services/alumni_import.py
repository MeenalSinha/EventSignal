"""Alumni batch import service for EventSignal Phase 8.

Processes institutional CSV directory uploads with dry-run validation, duplicate
detection, and strict adherence to user privacy and consent boundaries.

CRITICAL PRIVACY GUARANTEE:
Imported alumni identities NEVER automatically receive `willing_to_connect`
or public discoverability. They default to PRIVATE visibility and False consent.
"""

from __future__ import annotations

import contextlib
import csv
import io
import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.alumni_import import AlumniImportJob, ImportJobStatus
from app.models.alumni_profile import AlumniProfile, ProfileVisibility
from app.models.membership import InstitutionMembership, InstitutionRole, MembershipStatus
from app.models.user import User
from app.schemas.phase8 import (
    AlumniImportJobRead,
    AlumniImportPreviewResponse,
    AlumniImportRowPreview,
)


class AlumniImportService:
    @staticmethod
    def _parse_csv(csv_text: str) -> list[dict[str, str]]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        rows: list[dict[str, str]] = []
        for raw in reader:
            cleaned = {
                k.strip().lower().replace(" ", "_"): (v.strip() if v else "")
                for k, v in raw.items()
                if k
            }
            rows.append(cleaned)
        return rows

    @classmethod
    def preview(
        cls,
        db: Session,
        institution_id: str,
        filename: str,
        csv_text: str,
    ) -> AlumniImportPreviewResponse:
        parsed_rows = cls._parse_csv(csv_text)
        preview_records: list[AlumniImportRowPreview] = []
        seen_emails: set[str] = set()

        total = len(parsed_rows)
        valid = 0
        duplicates = 0
        invalid = 0

        for idx, row in enumerate(parsed_rows, start=1):
            email = row.get("email", "").lower().strip()
            full_name = row.get("full_name", "") or row.get("name", "")
            grad_year_str = row.get("grad_year", "") or row.get("graduation_year", "")
            degree = row.get("degree", "")
            current_role = row.get("current_role", "") or row.get("title", "")
            company = row.get("company", "") or row.get("organization", "")

            grad_year: int | None = None
            if grad_year_str:
                with contextlib.suppress(ValueError):
                    grad_year = int(grad_year_str)

            error_msg: str | None = None
            is_dup = False

            if not email or "@" not in email:
                error_msg = "Invalid or missing email address"
                invalid += 1
            elif not full_name:
                error_msg = "Missing full name"
                invalid += 1
            elif email in seen_emails:
                is_dup = True
                error_msg = "Duplicate entry in CSV file"
                duplicates += 1
            else:
                seen_emails.add(email)
                # Check existing membership in this institution
                existing_user = db.scalar(select(User).where(User.email == email))
                if existing_user:
                    existing_mem = db.scalar(
                        select(InstitutionMembership).where(
                            InstitutionMembership.institution_id == institution_id,
                            InstitutionMembership.user_id == existing_user.id,
                        )
                    )
                    if existing_mem:
                        is_dup = True
                        duplicates += 1

                if not is_dup:
                    valid += 1

            preview_records.append(
                AlumniImportRowPreview(
                    row_number=idx,
                    full_name=full_name or "Unknown",
                    email=email or "unknown@domain.edu",
                    grad_year=grad_year,
                    degree=degree or None,
                    current_role=current_role or None,
                    company=company or None,
                    is_duplicate=is_dup,
                    validation_error=error_msg,
                )
            )

        return AlumniImportPreviewResponse(
            filename=filename,
            total_rows=total,
            valid_rows=valid,
            duplicate_rows=duplicates,
            invalid_rows=invalid,
            preview_records=preview_records[:50],  # Return up to 50 preview rows
        )

    @classmethod
    def commit_import(
        cls,
        db: Session,
        institution_id: str,
        uploader_user_id: str,
        filename: str,
        csv_text: str,
    ) -> AlumniImportJobRead:
        parsed_rows = cls._parse_csv(csv_text)
        seen_emails: set[str] = set()

        total = len(parsed_rows)
        accepted = 0
        skipped = 0
        rejected = 0
        errors: list[dict[str, Any]] = []

        for idx, row in enumerate(parsed_rows, start=1):
            email = row.get("email", "").lower().strip()
            full_name = row.get("full_name", "") or row.get("name", "")
            grad_year_str = row.get("grad_year", "") or row.get("graduation_year", "")
            degree = row.get("degree", "")
            current_role = row.get("current_role", "") or row.get("title", "")
            company = row.get("company", "") or row.get("organization", "")

            grad_year: int | None = None
            if grad_year_str:
                with contextlib.suppress(ValueError):
                    grad_year = int(grad_year_str)

            if not email or "@" not in email or not full_name:
                rejected += 1
                errors.append(
                    {"row": idx, "email": email, "error": "Invalid format or missing name"}
                )
                continue

            if email in seen_emails:
                skipped += 1
                errors.append({"row": idx, "email": email, "warning": "Duplicate email in CSV"})
                continue

            seen_emails.add(email)

            # Check existing user
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                random_pw = secrets.token_urlsafe(32)
                user = User(
                    email=email,
                    hashed_password=hash_password(random_pw),
                    full_name=full_name,
                    is_active=True,
                )
                db.add(user)
                db.flush()

            # Check membership
            mem = db.scalar(
                select(InstitutionMembership).where(
                    InstitutionMembership.institution_id == institution_id,
                    InstitutionMembership.user_id == user.id,
                )
            )
            if mem:
                skipped += 1
                errors.append(
                    {"row": idx, "email": email, "warning": "User already has membership"}
                )
                continue

            mem = InstitutionMembership(
                institution_id=institution_id,
                user_id=user.id,
                role=InstitutionRole.ALUMNI,
                status=MembershipStatus.ACTIVE,
            )
            db.add(mem)
            db.flush()

            # Create or update AlumniProfile with ZERO DEFAULT CONSENT
            prof = db.scalar(
                select(AlumniProfile).where(
                    AlumniProfile.institution_id == institution_id,
                    AlumniProfile.user_id == user.id,
                )
            )
            if not prof:
                prof = AlumniProfile(
                    institution_id=institution_id,
                    user_id=user.id,
                    membership_id=mem.id,
                    display_name=full_name,
                    industry=company or degree or None,
                    professional_domain=current_role or None,
                    willing_to_connect=False,  # CRITICAL: explicit consent preserved
                    visibility=ProfileVisibility.PRIVATE,  # CRITICAL: private by default
                    extra_data={
                        "imported": True,
                        "grad_year": grad_year,
                        "degree": degree,
                        "company": company,
                        "current_role": current_role,
                    },
                )
                db.add(prof)

            accepted += 1

        job = AlumniImportJob(
            institution_id=institution_id,
            uploader_user_id=uploader_user_id,
            filename=filename,
            status=ImportJobStatus.COMMITTED,
            total_rows=total,
            accepted_rows=accepted,
            skipped_rows=skipped,
            rejected_rows=rejected,
            validation_errors=errors,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return AlumniImportJobRead.model_validate(job)
