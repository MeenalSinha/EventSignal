"""Phase 4: Tests for the opportunity assessment engine and API.

Tests are deliberately deterministic — they build evidence records
by hand, assert on score ranges and field categorisation, and check
API behaviour without any network or LLM calls.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import API_V1_PREFIX
from app.models.field_evidence import EvidenceStatus, ExtractionMethod, FieldEvidence
from app.models.opportunity import Opportunity
from app.models.opportunity_assessment import OpportunityAssessment
from app.models.source_reference import SourceReference, SourceType
from app.services.assessment import (
    CRITICAL_FIELDS,
    OPTIONAL_FIELDS,
    assess_opportunity,
)

ASSESS_URL_TMPL = API_V1_PREFIX + "/opportunities/{id}/assess"
GET_ASSESS_URL_TMPL = API_V1_PREFIX + "/opportunities/{id}/assessment"

ALL_FIELDS = list(CRITICAL_FIELDS | OPTIONAL_FIELDS)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_opportunity(session: Session) -> Opportunity:
    opp = Opportunity(title="Test Opportunity")
    session.add(opp)
    session.flush()
    return opp


def _make_source(session: Session, opportunity_id: str) -> SourceReference:
    src = SourceReference(
        opportunity_id=opportunity_id,
        source_type=SourceType.OPPORTUNITY_LISTING,
        url="https://example.com/opp",
        retrieved_at=datetime.now(UTC),
    )
    session.add(src)
    session.flush()
    return src


def _add_evidence(
    session: Session,
    opportunity_id: str,
    source_id: str,
    field_name: str,
    status: EvidenceStatus,
    method: ExtractionMethod = ExtractionMethod.RULE_BASED,
    value: str | None = None,
) -> FieldEvidence:
    ev = FieldEvidence(
        opportunity_id=opportunity_id,
        source_id=source_id,
        field_name=field_name,
        extracted_value=value,
        evidence_status=status,
        extraction_method=method,
    )
    session.add(ev)
    session.flush()
    return ev


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------


def test_assess_opportunity_not_found_raises(session: Session) -> None:
    with pytest.raises(LookupError, match="not found"):
        assess_opportunity("nonexistent-id", session)


def test_assess_fully_evidenced_opportunity(session: Session) -> None:
    """All fields found via STRUCTURED extraction → near-perfect scores."""
    opp = _make_opportunity(session)
    src = _make_source(session, opp.id)

    for fname in ALL_FIELDS:
        _add_evidence(
            session,
            opp.id,
            src.id,
            fname,
            EvidenceStatus.FOUND,
            ExtractionMethod.STRUCTURED,
            value="test value",
        )
    session.commit()

    result = assess_opportunity(opp.id, session)

    assert result.completeness_score == pytest.approx(1.0)
    assert result.evidence_quality_score == pytest.approx(1.0)
    assert result.consistency_score >= 0.8
    assert result.overall_score >= 0.9
    assert result.missing_critical_fields == []
    assert result.missing_optional_fields == []
    assert result.fields_found_count == len(ALL_FIELDS)


def test_assess_no_evidence_opportunity(session: Session) -> None:
    """No FieldEvidence → scores reflect zero knowledge."""
    opp = _make_opportunity(session)
    session.commit()

    result = assess_opportunity(opp.id, session)

    assert result.completeness_score == pytest.approx(0.0)
    assert result.evidence_quality_score == pytest.approx(0.0)
    assert result.fields_found_count == 0
    assert result.total_fields_assessed == 0
    # All critical fields should be listed as missing
    assert set(result.missing_critical_fields) == CRITICAL_FIELDS


def test_assess_partial_evidence(session: Session) -> None:
    """Some fields found, some not → intermediate scores."""
    opp = _make_opportunity(session)
    src = _make_source(session, opp.id)

    # Found: title, organizer
    for fname in ["title", "organizer"]:
        _add_evidence(
            session,
            opp.id,
            src.id,
            fname,
            EvidenceStatus.FOUND,
            value="Some value",
        )
    # Not found: all other critical fields
    for fname in CRITICAL_FIELDS - {"title", "organizer"}:
        _add_evidence(
            session,
            opp.id,
            src.id,
            fname,
            EvidenceStatus.NOT_FOUND,
        )
    session.commit()

    result = assess_opportunity(opp.id, session)

    assert 0.0 < result.completeness_score < 1.0
    assert result.fields_found_count == 2
    assert result.fields_not_found_count >= len(CRITICAL_FIELDS) - 2
    # registration_deadline and application_url must be in missing_critical
    assert "registration_deadline" in result.missing_critical_fields
    assert "application_url" in result.missing_critical_fields


def test_assess_conflicting_fields(session: Session) -> None:
    """Fields with SOURCES_DISAGREE → lower consistency score + correct classification."""
    opp = _make_opportunity(session)
    src = _make_source(session, opp.id)

    _add_evidence(
        session,
        opp.id,
        src.id,
        "registration_deadline",
        EvidenceStatus.SOURCES_DISAGREE,
    )
    _add_evidence(
        session,
        opp.id,
        src.id,
        "title",
        EvidenceStatus.FOUND,
        value="Test",
    )
    session.commit()

    result = assess_opportunity(opp.id, session)

    assert result.consistency_score < 0.5
    assert "registration_deadline" in result.conflicting_fields
    assert "registration_deadline" not in result.ambiguous_fields


def test_assess_ambiguous_fields(session: Session) -> None:
    """Fields with NEEDS_VERIFICATION → moderate consistency score + ambiguous list."""
    opp = _make_opportunity(session)
    src = _make_source(session, opp.id)

    _add_evidence(
        session,
        opp.id,
        src.id,
        "location",
        EvidenceStatus.NEEDS_VERIFICATION,
    )
    _add_evidence(
        session,
        opp.id,
        src.id,
        "title",
        EvidenceStatus.FOUND,
        value="Test",
    )
    session.commit()

    result = assess_opportunity(opp.id, session)

    assert "location" in result.ambiguous_fields
    assert "location" not in result.conflicting_fields
    assert result.consistency_score < 0.85


def test_assess_upserts_on_rerun(session: Session) -> None:
    """Re-running assessment replaces the previous record (upsert semantics)."""
    opp = _make_opportunity(session)
    session.commit()

    first = assess_opportunity(opp.id, session)
    first_id = first.id

    second = assess_opportunity(opp.id, session)

    from sqlalchemy import select

    all_records = session.scalars(
        select(OpportunityAssessment).where(
            OpportunityAssessment.opportunity_id == opp.id
        )
    ).all()

    assert len(all_records) == 1
    # IDs may differ (new row inserted) but only one exists
    assert all_records[0].opportunity_id == opp.id


def test_overall_score_formula_bounds(session: Session) -> None:
    """Overall score is always within [0.0, 1.0]."""
    opp = _make_opportunity(session)
    session.commit()

    result = assess_opportunity(opp.id, session)
    assert 0.0 <= result.overall_score <= 1.0
    assert 0.0 <= result.completeness_score <= 1.0
    assert 0.0 <= result.evidence_quality_score <= 1.0
    assert 0.0 <= result.consistency_score <= 1.0


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


def test_api_assess_not_found(client: TestClient) -> None:
    resp = client.post(ASSESS_URL_TMPL.format(id="no-such-id"))
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_api_assess_and_retrieve(client: TestClient, session: Session) -> None:
    """POST /assess creates a record; GET /assessment retrieves it."""
    opp = _make_opportunity(session)
    session.commit()

    # Trigger assessment
    resp = client.post(ASSESS_URL_TMPL.format(id=opp.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["opportunity_id"] == opp.id
    assert "overall_score" in data
    assert "completeness_explanation" in data
    assert "missing_critical_fields" in data
    assert isinstance(data["missing_critical_fields"], list)
    assert isinstance(data["missing_optional_fields"], list)

    # Retrieve
    get_resp = client.get(GET_ASSESS_URL_TMPL.format(id=opp.id))
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["opportunity_id"] == opp.id
    assert get_data["overall_score"] == data["overall_score"]


def test_api_get_assessment_before_assess_is_404(client: TestClient, session: Session) -> None:
    opp = _make_opportunity(session)
    session.commit()

    resp = client.get(GET_ASSESS_URL_TMPL.format(id=opp.id))
    assert resp.status_code == 404
    assert "assess" in resp.json()["detail"].lower()


def test_api_get_assessment_for_nonexistent_opportunity(client: TestClient) -> None:
    resp = client.get(GET_ASSESS_URL_TMPL.format(id="ghost-id"))
    assert resp.status_code == 404


def test_api_reassess_replaces_previous(client: TestClient, session: Session) -> None:
    opp = _make_opportunity(session)
    session.commit()

    first_resp = client.post(ASSESS_URL_TMPL.format(id=opp.id))
    assert first_resp.status_code == 200

    second_resp = client.post(ASSESS_URL_TMPL.format(id=opp.id))
    assert second_resp.status_code == 200

    # Only one assessment exists for the opportunity
    from sqlalchemy import select

    count = len(
        session.scalars(
            select(OpportunityAssessment).where(
                OpportunityAssessment.opportunity_id == opp.id
            )
        ).all()
    )
    assert count == 1


def test_api_assessment_score_types(client: TestClient, session: Session) -> None:
    """Scores returned by the API are numeric floats in [0, 1]."""
    opp = _make_opportunity(session)
    session.commit()

    resp = client.post(ASSESS_URL_TMPL.format(id=opp.id))
    data = resp.json()
    for key in ("overall_score", "completeness_score", "evidence_quality_score", "consistency_score"):
        assert isinstance(data[key], float), f"{key} should be float"
        assert 0.0 <= data[key] <= 1.0, f"{key} out of range"


def test_api_assessment_has_explanations(client: TestClient, session: Session) -> None:
    """All explanation fields are non-empty strings."""
    opp = _make_opportunity(session)
    session.commit()

    resp = client.post(ASSESS_URL_TMPL.format(id=opp.id))
    data = resp.json()
    for key in (
        "completeness_explanation",
        "evidence_quality_explanation",
        "consistency_explanation",
        "limitations",
    ):
        assert isinstance(data[key], str), f"{key} should be str"
        assert len(data[key]) > 0, f"{key} should not be empty"
