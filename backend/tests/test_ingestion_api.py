"""Integration tests for opportunity ingestion API and service (Phase 3)."""

from __future__ import annotations

from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import API_V1_PREFIX
from app.models.field_evidence import EvidenceStatus, FieldEvidence
from app.models.opportunity import Opportunity, OpportunityType
from app.models.source_reference import SourceReference
from app.services.ingestion import ingest_opportunity_url, normalize_url

INGEST_URL = f"{API_V1_PREFIX}/opportunities/ingest"
LIST_URL = f"{API_V1_PREFIX}/opportunities"

MOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NextGen AI Fellowship 2026</title>
    <meta property="og:description" content="A prestigious research fellowship in AI." />
    <meta property="og:site_name" content="Tech Research Institute" />
</head>
<body>
    <h1>NextGen AI Fellowship 2026</h1>
    <section>
        <h2>Registration Deadline</h2>
        <p>Registration deadline: November 15, 2026</p>
    </section>
    <section>
        <h2>Eligibility</h2>
        <p>Open to undergraduate and graduate researchers worldwide.</p>
    </section>
    <section>
        <h2>Skills Required</h2>
        <p>Machine Learning, PyTorch, Python.</p>
    </section>
    <a href="/apply">Apply Now</a>
</body>
</html>
"""


def test_normalize_url() -> None:
    raw = "HTTPS://Example.COM:443/event/hackathon/?utm_source=twitter&ref=newsletter#details"
    normalized = normalize_url(raw)
    assert normalized == "https://example.com/event/hackathon"


def test_ingest_opportunity_service_creates_records(session: Session, settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=MOCK_HTML, headers={"Content-Type": "text/html"})

    transport = httpx.MockTransport(handler)

    res = ingest_opportunity_url(
        url="https://example.com/fellowship",
        session=session,
        settings=settings,
        transport=transport,
    )

    assert res.is_duplicate is False
    assert res.opportunity.title == "NextGen AI Fellowship 2026"
    assert res.opportunity.opportunity_type == OpportunityType.FELLOWSHIP
    assert res.opportunity.organizer == "Tech Research Institute"
    assert res.source_reference.url == "https://example.com/fellowship"

    # Database records verified
    opp_in_db = session.scalars(select(Opportunity)).first()
    assert opp_in_db is not None
    assert opp_in_db.title == "NextGen AI Fellowship 2026"

    # Source reference verified
    source_in_db = session.scalars(select(SourceReference)).first()
    assert source_in_db is not None
    assert source_in_db.opportunity_id == opp_in_db.id

    # Evidence records verified
    evidence_rows = session.scalars(select(FieldEvidence)).all()
    assert len(evidence_rows) > 0
    title_ev = next(e for e in evidence_rows if e.field_name == "title")
    assert title_ev.evidence_status == EvidenceStatus.FOUND
    assert title_ev.extracted_value == "NextGen AI Fellowship 2026"


def test_ingest_duplicate_url_returns_existing_record(session: Session, settings: Settings) -> None:
    network_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal network_called
        network_called = True
        return httpx.Response(200, text=MOCK_HTML, headers={"Content-Type": "text/html"})

    transport = httpx.MockTransport(handler)

    # First ingestion
    first_res = ingest_opportunity_url(
        url="https://example.com/fellowship?utm_source=twitter",
        session=session,
        settings=settings,
        transport=transport,
    )
    assert first_res.is_duplicate is False
    assert network_called is True

    # Second ingestion with same normalized URL -> must be duplicate without network call
    network_called = False
    second_res = ingest_opportunity_url(
        url="https://example.com/fellowship#about",
        session=session,
        settings=settings,
        transport=transport,
    )
    assert second_res.is_duplicate is True
    assert second_res.opportunity.id == first_res.opportunity.id
    assert network_called is False  # Network was not called!


def test_ingest_api_endpoint_success(client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=MOCK_HTML, headers={"Content-Type": "text/html"})

    # Patch retrieve_web_page transport or validate_hostname_dns
    with patch("app.services.ingestion.retrieve_web_page") as mock_retrieve:
        from datetime import UTC, datetime

        from app.services.retrieval import RetrievalResult

        mock_retrieve.return_value = RetrievalResult(
            submitted_url="https://example.com/fellowship",
            final_url="https://example.com/fellowship",
            status_code=200,
            content=MOCK_HTML,
            content_hash="a" * 64,
            content_type="text/html",
            retrieved_at=datetime.now(UTC),
            headers={"content-type": "text/html"},
        )

        resp = client.post(
            INGEST_URL,
            json={"url": "https://example.com/fellowship"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_duplicate"] is False
        assert data["opportunity"]["title"] == "NextGen AI Fellowship 2026"
        assert len(data["evidence"]) > 0

        # Now query GET /api/v1/opportunities
        list_resp = client.get(LIST_URL)
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["title"] == "NextGen AI Fellowship 2026"
        assert len(list_data["items"][0]["evidence"]) > 0


def test_ingest_api_endpoint_rejects_ssrf(client: TestClient) -> None:
    resp = client.post(
        INGEST_URL,
        json={"url": "http://127.0.0.1:8080/admin"},
    )
    assert resp.status_code == 400
    assert (
        "private, internal, or loopback" in resp.json()["detail"]
        or "Destination port" in resp.json()["detail"]
    )


def test_ingest_api_endpoint_rejects_invalid_url(client: TestClient) -> None:
    resp = client.post(
        INGEST_URL,
        json={"url": "not-a-valid-url"},
    )
    assert resp.status_code == 422
