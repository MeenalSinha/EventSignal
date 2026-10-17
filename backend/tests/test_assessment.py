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
    assert second.id is not None
    assert first_id is not None

    from sqlalchemy import select

    all_records = session.scalars(
        select(OpportunityAssessment).where(OpportunityAssessment.opportunity_id == opp.id)
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
            select(OpportunityAssessment).where(OpportunityAssessment.opportunity_id == opp.id)
        ).all()
    )
    assert count == 1


def test_api_assessment_score_types(client: TestClient, session: Session) -> None:
    """Scores returned by the API are numeric floats in [0, 1]."""
    opp = _make_opportunity(session)
    session.commit()

    resp = client.post(ASSESS_URL_TMPL.format(id=opp.id))
    data = resp.json()
    for key in (
        "overall_score",
        "completeness_score",
        "evidence_quality_score",
        "consistency_score",
    ):
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


def test_assessment_policy_validation() -> None:
    """AssessmentPolicy enforces strict validation on weights and fields."""
    from pydantic import ValidationError

    from app.core.assessment_policy import AssessmentPolicy

    # Invalid dimension weights (do not sum to 1.0)
    with pytest.raises(ValidationError):
        AssessmentPolicy(
            policy_version="test-invalid",
            dimension_weights={"completeness": 0.5, "evidence_quality": 0.2, "consistency": 0.1},
        )

    # Invalid field name in critical_fields
    with pytest.raises(ValidationError):
        AssessmentPolicy(
            policy_version="test-invalid-field",
            critical_fields=["not_a_real_field"],
        )

    # Valid policy loads correctly
    policy = AssessmentPolicy(
        policy_version="custom-2.0",
        dimension_weights={"completeness": 0.6, "evidence_quality": 0.3, "consistency": 0.1},
    )
    assert policy.policy_version == "custom-2.0"
    assert policy.dimension_weights["completeness"] == 0.6


def test_changing_policy_weights_changes_scores(session: Session) -> None:
    """Modifying policy weights produces different assessment scores without code changes."""
    from app.core.assessment_policy import AssessmentPolicy

    opp = _make_opportunity(session)
    src = _make_source(session, opp.id)
    _add_evidence(
        session,
        opp.id,
        src.id,
        "title",
        EvidenceStatus.FOUND,
        value="Found Title",
    )
    session.commit()

    # Policy emphasizing completeness
    policy_high_comp = AssessmentPolicy(
        policy_version="high-comp",
        dimension_weights={"completeness": 0.8, "evidence_quality": 0.1, "consistency": 0.1},
    )
    res1 = assess_opportunity(opp.id, session, policy=policy_high_comp)

    # Policy emphasizing consistency
    policy_high_cons = AssessmentPolicy(
        policy_version="high-cons",
        dimension_weights={"completeness": 0.1, "evidence_quality": 0.1, "consistency": 0.8},
    )
    res2 = assess_opportunity(opp.id, session, policy=policy_high_cons)

    # Consistency score for single source is 0.85; completeness is low (1/13 ~ 0.08)
    # res2 should score noticeably higher overall than res1
    assert res1.overall_score != res2.overall_score
    assert res2.overall_score > res1.overall_score


def test_multi_source_cross_source_agreement(session: Session) -> None:
    """Multiple sources with matching extracted values achieve full consistency."""
    opp = _make_opportunity(session)
    s1 = SourceReference(
        opportunity_id=opp.id,
        source_type=SourceType.OPPORTUNITY_LISTING,
        url="https://source1.example/event",
        title="Source 1",
    )
    s2 = SourceReference(
        opportunity_id=opp.id,
        source_type=SourceType.OPPORTUNITY_LISTING,
        url="https://source2.example/event",
        title="Source 2",
    )
    session.add_all([s1, s2])
    session.flush()

    # Both sources agree on location
    _add_evidence(
        session,
        opp.id,
        s1.id,
        "location",
        EvidenceStatus.FOUND,
        value="Bengaluru, India",
    )
    _add_evidence(
        session,
        opp.id,
        s2.id,
        "location",
        EvidenceStatus.FOUND,
        value="Bengaluru, India",
    )
    session.commit()

    res = assess_opportunity(opp.id, session)
    assert res.consistency_score == 1.0
    assert len(res.conflicting_fields) == 0
    assert "agree" in res.consistency_explanation.lower()


def test_multi_source_cross_source_conflict_detection(session: Session) -> None:
    """Contradictory values from different sources trigger conflict classification and details."""
    opp = _make_opportunity(session)
    s1 = SourceReference(
        opportunity_id=opp.id,
        source_type=SourceType.OPPORTUNITY_LISTING,
        url="https://source1.example/event",
        title="Source 1",
    )
    s2 = SourceReference(
        opportunity_id=opp.id,
        source_type=SourceType.OPPORTUNITY_LISTING,
        url="https://source2.example/event",
        title="Source 2",
    )
    session.add_all([s1, s2])
    session.flush()

    # Source 1 says $5,000; Source 2 says $10,000
    _add_evidence(
        session,
        opp.id,
        s1.id,
        "compensation",
        EvidenceStatus.FOUND,
        value="$5,000 Prize Pool",
    )
    _add_evidence(
        session,
        opp.id,
        s2.id,
        "compensation",
        EvidenceStatus.FOUND,
        value="$10,000 Cash Prizes",
    )
    session.commit()

    res = assess_opportunity(opp.id, session)
    assert "compensation" in res.conflicting_fields
    assert res.consistency_score < 1.0
    assert len(res.conflict_details) == 1
    assert res.conflict_details[0]["field_name"] == "compensation"
    assert "disagree" in res.consistency_explanation.lower()


def test_attach_additional_source_endpoint(client: TestClient, session: Session) -> None:
    """POST /opportunities/{id}/sources attaches an additional source to an opportunity."""
    import httpx

    from app.core.config import get_settings
    from app.services.ingestion import ingest_opportunity_url

    opp = _make_opportunity(session)
    session.commit()

    # Mock response for second source
    mock_html = """
    <html>
      <head><title>Second Source View</title></head>
      <body>
        <h1>Same Hackathon</h1>
        <p>Location: Virtual Online</p>
      </body>
    </html>
    """
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            text=mock_html,
            headers={"Content-Type": "text/html"},
        )
    )

    with client:
        res = ingest_opportunity_url(
            url="https://secondary-source.example/info",
            session=session,
            settings=get_settings(),
            opportunity_id=opp.id,
            transport=transport,
        )
        assert res.opportunity.id == opp.id
        assert len(res.opportunity.sources) == 1  # 1 new source added to opp
        assert res.source_reference.url == "https://secondary-source.example/info"
