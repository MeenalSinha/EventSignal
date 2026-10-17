"""Tests for generic staged opportunity extraction (Phase 3)."""

from __future__ import annotations

from app.models.field_evidence import EvidenceStatus, ExtractionMethod
from app.models.opportunity import OpportunityType, ParticipationMode
from app.services.extractor import extract_opportunity_from_html


def test_extract_from_json_ld_event() -> None:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": "Global AI Hackathon 2026",
            "description": "A 48-hour global AI and ML competition.",
            "startDate": "2026-11-01T09:00:00Z",
            "endDate": "2026-11-03T18:00:00Z",
            "organizer": {
                "@type": "Organization",
                "name": "OpenAI & Partners"
            },
            "location": {
                "@type": "Place",
                "name": "San Francisco Convention Center"
            },
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode"
        }
        </script>
    </head>
    <body>
        <h1>Global AI Hackathon 2026</h1>
    </body>
    </html>
    """
    res = extract_opportunity_from_html(html, "https://example.com/hackathon")

    assert res.structured_data_found is True
    assert res.fields["title"].value == "Global AI Hackathon 2026"
    assert res.fields["title"].evidence_status == EvidenceStatus.FOUND
    assert res.fields["title"].extraction_method == ExtractionMethod.STRUCTURED

    assert res.fields["opportunity_type"].value == OpportunityType.HACKATHON
    assert res.fields["organizer"].value == "OpenAI & Partners"
    assert res.fields["organizer"].evidence_status == EvidenceStatus.FOUND

    assert res.fields["start_date"].value is not None
    assert res.fields["end_date"].value is not None
    assert res.fields["location"].value == "San Francisco Convention Center"
    assert res.fields["mode"].value == ParticipationMode.OFFLINE

    # Absent fields must remain NOT_FOUND without fabrication
    assert res.fields["compensation"].value is None
    assert res.fields["compensation"].evidence_status == EvidenceStatus.NOT_FOUND


def test_extract_from_metadata_open_graph() -> None:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="Quantum Computing Research Fellowship" />
        <meta property="og:description" content="Quantum fellowship researching algorithms." />
        <meta property="og:site_name" content="National Quantum Lab" />
        <link rel="canonical" href="https://example.com/fellowship/apply" />
    </head>
    <body>
        <div>Content about fellowship</div>
    </body>
    </html>
    """
    res = extract_opportunity_from_html(html, "https://example.com/fellowship")

    assert res.structured_data_found is False
    assert res.fields["title"].value == "Quantum Computing Research Fellowship"
    assert res.fields["opportunity_type"].value == OpportunityType.FELLOWSHIP
    assert res.fields["organizer"].value == "National Quantum Lab"
    assert res.fields["application_url"].value == "https://example.com/fellowship/apply"

    # Deadlines not present -> NOT_FOUND
    assert res.fields["registration_deadline"].value is None
    assert res.fields["registration_deadline"].evidence_status == EvidenceStatus.NOT_FOUND


def test_extract_from_heuristics_dates_eligibility_skills() -> None:
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Deep Learning Bootcamp</title></head>
    <body>
        <h1>Deep Learning Bootcamp</h1>
        <section>
            <h2>Registration Deadline</h2>
            <p>Registration deadline: October 25, 2026</p>
        </section>
        <section>
            <h2>Eligibility</h2>
            <p>Undergraduate and graduate students with programming background.</p>
        </section>
        <section>
            <h2>Skills Required</h2>
            <p>Python, PyTorch, Linear Algebra.</p>
        </section>
        <section>
            <h2>Prizes & Rewards</h2>
            <p>Total prize pool of $10,000 for top projects.</p>
        </section>
        <div>
            <p>This is an online virtual workshop.</p>
            <a href="/register">Apply Now</a>
        </div>
    </body>
    </html>
    """
    res = extract_opportunity_from_html(html, "https://bootcamp.org/info")

    assert res.fields["title"].value == "Deep Learning Bootcamp"
    assert res.fields["opportunity_type"].value == OpportunityType.WORKSHOP

    # Registration deadline extracted from human date
    reg_dl = res.fields["registration_deadline"].value
    assert reg_dl is not None
    assert reg_dl.year == 2026
    assert reg_dl.month == 10
    assert reg_dl.day == 25

    # Eligibility and skills
    assert "Undergraduate" in str(res.fields["eligibility"].value)
    assert "Python, PyTorch" in str(res.fields["skills_required"].value)
    assert "$10,000" in str(res.fields["compensation"].value)

    # Action link
    assert res.fields["application_url"].value == "https://bootcamp.org/register"
    assert res.fields["mode"].value == ParticipationMode.ONLINE


def test_extract_empty_or_malformed_page_does_not_invent_data() -> None:
    html = (
        "<html><body><p>Random uninformative text without dates or opportunities.</p></body></html>"
    )
    res = extract_opportunity_from_html(html, "https://empty.test/page")

    # Title is not found
    assert res.fields["title"].value is None
    assert res.fields["title"].evidence_status == EvidenceStatus.NOT_FOUND

    # Deadlines are NOT invented
    assert res.fields["registration_deadline"].value is None
    assert res.fields["registration_deadline"].evidence_status == EvidenceStatus.NOT_FOUND
    assert res.fields["submission_deadline"].value is None
    assert res.fields["submission_deadline"].evidence_status == EvidenceStatus.NOT_FOUND
    assert res.fields["organizer"].value is None
    assert res.fields["organizer"].evidence_status == EvidenceStatus.NOT_FOUND


def test_extract_malformed_json_ld_recovers_gracefully() -> None:
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        { malformed json without closing
        </script>
        <title>Cybersecurity Competition 2026</title>
    </head>
    <body>
        <h1>Cybersecurity Competition 2026</h1>
    </body>
    </html>
    """
    res = extract_opportunity_from_html(html, "https://cyber.test")
    # Should not raise exception, should fall back to HTML title
    assert res.fields["title"].value == "Cybersecurity Competition 2026"
    assert res.fields["opportunity_type"].value == OpportunityType.COMPETITION
