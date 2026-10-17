"""Opportunity intake and evidence collection service.

Orchestrates:
1. URL normalization and duplicate-submission detection.
2. Safe SSRF-protected HTTP retrieval (via retrieval.py).
3. Generic multi-stage content extraction (via extractor.py).
4. Atomic database persistence of Opportunity, SourceReference, and FieldEvidence.
5. Honest reporting of extracted vs. missing fields without data fabrication.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.field_evidence import EvidenceStatus, FieldEvidence
from app.models.opportunity import Opportunity
from app.models.source_reference import SourceReference, SourceType
from app.schemas.ingest import OpportunityIngestResponse
from app.schemas.opportunity import (
    FieldEvidenceRead,
    OpportunityRead,
    SourceReferenceRead,
)
from app.services.extractor import (
    OPPORTUNITY_FIELDS,
    extract_opportunity_from_html,
)
from app.services.retrieval import retrieve_web_page

logger = logging.getLogger(__name__)

TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def normalize_url(raw_url: str) -> str:
    """Normalize URL for consistent deduplication and provenance.

    - Lowercases scheme and netloc.
    - Strips default ports (:80 on http, :443 on https).
    - Removes common tracking query parameters.
    - Strips fragment identifiers.
    - Strips trailing slash on non-root paths.
    """
    clean = raw_url.strip()
    parsed = urlparse(clean)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    if (scheme == "http" and netloc.endswith(":80")) or (
        scheme == "https" and netloc.endswith(":443")
    ):
        netloc = netloc.rsplit(":", 1)[0]

    path = parsed.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    query_parts: list[str] = []
    if parsed.query:
        for qp in parsed.query.split("&"):
            if not qp:
                continue
            if "=" in qp:
                k, _ = qp.split("=", 1)
                if k.lower() not in TRACKING_QUERY_PARAMS:
                    query_parts.append(qp)
            elif qp.lower() not in TRACKING_QUERY_PARAMS:
                query_parts.append(qp)
    query = "&".join(query_parts)

    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def _format_extracted_value(val: Any) -> str | None:
    """Format an extracted Python value into a string representation for FieldEvidence."""
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return str(val.isoformat())
    if hasattr(val, "value"):
        return str(val.value)
    return str(val)


def ingest_opportunity_url(
    url: str,
    session: Session,
    settings: Settings,
    force_refresh: bool = False,
    opportunity_id: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> OpportunityIngestResponse:
    """Ingest a public opportunity URL, extract details, and persist with evidence.

    Handles duplicates deterministically: returns existing record unless force_refresh is True.
    If opportunity_id is specified, associates the source with the existing opportunity.
    All database writes are executed inside an atomic transaction.
    """
    normalized = normalize_url(url)

    target_opp: Opportunity | None = None
    if opportunity_id is not None:
        target_opp = session.scalars(
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(selectinload(Opportunity.sources), selectinload(Opportunity.evidence))
        ).first()
        if target_opp is None:
            raise LookupError(f"Opportunity {opportunity_id!r} not found")

    # 1. Check for existing source by normalized URL
    if target_opp is not None:
        existing_source = session.scalars(
            select(SourceReference).where(
                SourceReference.opportunity_id == target_opp.id,
                SourceReference.url == normalized,
            )
        ).first()
    else:
        existing_source = session.scalars(
            select(SourceReference).where(SourceReference.url == normalized)
        ).first()

    if existing_source is not None and not force_refresh:
        opp = session.scalars(
            select(Opportunity)
            .where(Opportunity.id == existing_source.opportunity_id)
            .options(selectinload(Opportunity.sources), selectinload(Opportunity.evidence))
        ).first()

        if opp is not None:
            found_count = sum(1 for e in opp.evidence if e.evidence_status == EvidenceStatus.FOUND)
            return OpportunityIngestResponse(
                opportunity=OpportunityRead.model_validate(opp),
                source_reference=SourceReferenceRead.model_validate(existing_source),
                is_duplicate=True,
                fields_extracted_count=found_count,
                evidence=[FieldEvidenceRead.model_validate(e) for e in opp.evidence],
                message=(
                    "Opportunity source already ingested. "
                    "Returned existing record without re-fetching."
                ),
            )

    # 2. Retrieve page content safely
    retrieval = retrieve_web_page(url=url, settings=settings, transport=transport)

    # 3. Extract opportunity fields and field-level evidence
    extraction = extract_opportunity_from_html(
        html=retrieval.content,
        source_url=retrieval.final_url,
    )

    # 4. Atomic database persistence
    source_title = extraction.raw_title or retrieval.final_url
    if len(source_title) > 500:
        source_title = source_title[:497] + "..."

    metadata = {
        "submitted_url": url,
        "final_url": retrieval.final_url,
        "status_code": retrieval.status_code,
        "content_type": retrieval.content_type,
        "structured_data_found": extraction.structured_data_found,
    }

    try:
        if existing_source is not None and force_refresh:
            # Refresh existing opportunity source
            opp = session.scalars(
                select(Opportunity)
                .where(Opportunity.id == existing_source.opportunity_id)
                .options(selectinload(Opportunity.sources), selectinload(Opportunity.evidence))
            ).first()

            if opp is None:
                raise RuntimeError(
                    f"SourceReference {existing_source.id} refers to missing Opportunity"
                )

            # Update opportunity fields if not previously set
            for field in OPPORTUNITY_FIELDS:
                extracted = extraction.fields[field]
                if extracted.value is not None and getattr(opp, field) is None:
                    setattr(opp, field, extracted.value)

            # Update source reference
            existing_source.title = source_title
            existing_source.retrieved_at = retrieval.retrieved_at
            existing_source.content_hash = retrieval.content_hash
            existing_source.source_metadata = metadata

            # Clear old evidence for this specific source and re-populate
            session.execute(
                delete(FieldEvidence).where(
                    FieldEvidence.opportunity_id == opp.id,
                    FieldEvidence.source_id == existing_source.id,
                )
            )

            target_source_id = existing_source.id
            active_source_ref = existing_source
        elif target_opp is not None:
            # Attach new source to existing opportunity
            opp = target_opp

            # Fill in unpopulated opportunity fields without overwriting established ones
            for field in OPPORTUNITY_FIELDS:
                extracted = extraction.fields[field]
                if extracted.value is not None and getattr(opp, field) is None:
                    setattr(opp, field, extracted.value)

            source_ref = SourceReference(
                opportunity_id=opp.id,
                source_type=SourceType.OPPORTUNITY_LISTING,
                url=normalized,
                title=source_title,
                retrieved_at=retrieval.retrieved_at,
                content_hash=retrieval.content_hash,
                source_metadata=metadata,
            )
            session.add(source_ref)
            opp.sources.append(source_ref)
            session.flush()

            target_source_id = source_ref.id
            active_source_ref = source_ref
        else:
            # Create new opportunity
            opp_kwargs: dict[str, Any] = {}
            for field in OPPORTUNITY_FIELDS:
                extracted = extraction.fields[field]
                opp_kwargs[field] = extracted.value

            opp = Opportunity(**opp_kwargs)
            session.add(opp)
            session.flush()  # Generate opp.id

            source_ref = SourceReference(
                opportunity_id=opp.id,
                source_type=SourceType.OPPORTUNITY_LISTING,
                url=normalized,
                title=source_title,
                retrieved_at=retrieval.retrieved_at,
                content_hash=retrieval.content_hash,
                source_metadata=metadata,
            )
            session.add(source_ref)
            opp.sources.append(source_ref)
            session.flush()  # Generate source_ref.id

            target_source_id = source_ref.id
            active_source_ref = source_ref

        # Persist FieldEvidence records for all evaluated fields
        for field in OPPORTUNITY_FIELDS:
            extracted = extraction.fields[field]
            evidence_rec = FieldEvidence(
                opportunity_id=opp.id,
                source_id=target_source_id,
                field_name=field,
                extracted_value=_format_extracted_value(extracted.value),
                supporting_excerpt=extracted.supporting_excerpt,
                extraction_method=extracted.extraction_method,
                evidence_status=extracted.evidence_status,
            )
            session.add(evidence_rec)
            opp.evidence.append(evidence_rec)

        session.commit()
        session.expire_all()

        # Reload with relationships loaded
        saved_opp = session.scalars(
            select(Opportunity)
            .where(Opportunity.id == opp.id)
            .options(selectinload(Opportunity.sources), selectinload(Opportunity.evidence))
        ).one()

        found_count = sum(
            1 for e in saved_opp.evidence if e.evidence_status == EvidenceStatus.FOUND
        )
        msg = (
            "Opportunity refreshed successfully from source."
            if (existing_source is not None and force_refresh)
            else "Opportunity ingested and evidence recorded successfully."
        )

        return OpportunityIngestResponse(
            opportunity=OpportunityRead.model_validate(saved_opp),
            source_reference=SourceReferenceRead.model_validate(active_source_ref),
            is_duplicate=False,
            fields_extracted_count=found_count,
            evidence=[FieldEvidenceRead.model_validate(e) for e in saved_opp.evidence],
            message=msg,
        )
    except Exception:
        session.rollback()
        raise
