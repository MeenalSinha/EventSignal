from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import (
    AlumniProfileVisibility,
    ConnectionPurpose,
    Opportunity,
    OpportunityType,
    ParticipationMode,
    RequestStatus,
    SourceReference,
    SourceType,
    StudentProfileVisibility,
)
from app.schemas import (
    AlumniProfileCreate,
    ConnectionRequestCreate,
    ConnectionRequestRead,
    OpportunityCreate,
    OpportunityRead,
    SourceReferenceCreate,
    StudentProfileCreate,
)

NOW = datetime(2030, 1, 1, tzinfo=UTC)


def test_empty_opportunity_is_valid() -> None:
    assert OpportunityCreate().sources == []


def test_valid_opportunity_with_sources() -> None:
    opp = OpportunityCreate(
        title="AI Hackathon 2030",
        opportunity_type=OpportunityType.HACKATHON,
        mode=ParticipationMode.ONLINE,
        start_date=NOW,
        end_date=NOW + timedelta(days=1),
        application_url="https://example.test/apply",
        sources=[{"source_type": "opportunity_listing", "url": "https://example.test"}],
    )
    assert opp.mode is ParticipationMode.ONLINE
    assert opp.opportunity_type is OpportunityType.HACKATHON


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "ftp://example.test/x",
        "data:text/html,hi",
        "http://",
        "https://user:pass@example.test/",
        "not a url",
        "https://example.test/" + "a" * 2100,
    ],
)
def test_unsafe_or_malformed_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        OpportunityCreate(application_url=url)
    with pytest.raises(ValidationError):
        SourceReferenceCreate(source_type=SourceType.OTHER, url=url)


def test_end_before_start_is_rejected() -> None:
    with pytest.raises(ValidationError, match="end_date"):
        OpportunityCreate(start_date=NOW, end_date=NOW - timedelta(hours=1))


@pytest.mark.parametrize(
    "field", ["start_date", "end_date", "registration_deadline", "submission_deadline"]
)
def test_naive_datetimes_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError, match="timezone"):
        OpportunityCreate(**{field: datetime(2030, 1, 1)})


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        OpportunityCreate(mode="sideways")  # type: ignore[arg-type]


def test_source_needs_url_unless_manual_text() -> None:
    with pytest.raises(ValidationError, match="url is required"):
        SourceReferenceCreate(source_type=SourceType.OPPORTUNITY_LISTING)
    assert SourceReferenceCreate(source_type=SourceType.MANUAL_TEXT).url is None


def test_opportunity_read_is_built_from_orm_without_exposing_extras(session) -> None:  # type: ignore[no-untyped-def]
    opp = Opportunity(title="Tech Fellowship", opportunity_type=OpportunityType.FELLOWSHIP)
    opp.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://a.test"))
    session.add(opp)
    session.commit()
    data = OpportunityRead.model_validate(opp).model_dump()
    assert data["title"] == "Tech Fellowship"
    assert data["opportunity_type"] == OpportunityType.FELLOWSHIP
    assert data["sources"][0]["url"] == "https://a.test"
    assert "_sa_instance_state" not in data


def test_student_profile_schema_validation() -> None:
    profile = StudentProfileCreate(
        display_name="Meenal",
        skills="Python, React",
        career_goals="ML Engineer",
        visibility=StudentProfileVisibility.ALUMNI_ONLY,
    )
    assert profile.display_name == "Meenal"
    assert profile.visibility == StudentProfileVisibility.ALUMNI_ONLY


def test_alumni_profile_willing_to_connect_validation() -> None:
    # Monthly connection limit requires willing_to_connect=True
    with pytest.raises(ValidationError, match="monthly_connection_limit"):
        AlumniProfileCreate(willing_to_connect=False, monthly_connection_limit=5)

    valid = AlumniProfileCreate(
        display_name="Dr. Jane Doe",
        professional_domain="Artificial Intelligence",
        willing_to_connect=True,
        monthly_connection_limit=5,
        visibility=AlumniProfileVisibility.STUDENTS_ONLY,
    )
    assert valid.willing_to_connect is True
    assert valid.monthly_connection_limit == 5


def test_connection_request_schema_validation() -> None:
    # Other purpose requires a message
    with pytest.raises(ValidationError, match="explaining the purpose"):
        ConnectionRequestCreate(
            requester_profile_id="student-1",
            recipient_profile_id="alumni-1",
            purpose=ConnectionPurpose.OTHER,
            message=None,
        )

    # Cannot connect to self
    with pytest.raises(ValidationError, match="cannot send a connection request to themselves"):
        ConnectionRequestCreate(
            requester_profile_id="user-1",
            recipient_profile_id="user-1",
            purpose=ConnectionPurpose.CAREER_GUIDANCE,
        )

    valid = ConnectionRequestCreate(
        requester_profile_id="student-1",
        recipient_profile_id="alumni-1",
        purpose=ConnectionPurpose.CAREER_GUIDANCE,
        message="I'd love to learn about your path into AI research.",
    )
    assert valid.purpose == ConnectionPurpose.CAREER_GUIDANCE
    assert valid.message == "I'd love to learn about your path into AI research."

    read = ConnectionRequestRead(
        id="req-1",
        requester_profile_id="student-1",
        recipient_profile_id="alumni-1",
        purpose=ConnectionPurpose.CAREER_GUIDANCE,
        message="I'd love to learn about your path into AI research.",
        status=RequestStatus.PENDING,
        responded_at=None,
        created_at=NOW,
        updated_at=NOW,
    )
    assert read.status == RequestStatus.PENDING
