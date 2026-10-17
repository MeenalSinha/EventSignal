"""Model behaviour for Phase 2 domain-model foundation.

Rows here are explicit synthetic fixtures living only in the isolated
test database; nothing in the application ever creates them.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    AlumniProfile,
    AlumniProfileVisibility,
    ConnectionPurpose,
    ConnectionRequest,
    EvidenceStatus,
    ExtractionMethod,
    FieldEvidence,
    MatchedEntityType,
    MatchExplanation,
    Opportunity,
    OpportunityType,
    ParticipationMode,
    RequestStatus,
    SourceReference,
    SourceType,
    StudentProfile,
    StudentProfileVisibility,
)

# ---------------------------------------------------------------------------
# Opportunity tests (evolved from Phase 1 Event)
# ---------------------------------------------------------------------------


def test_opportunity_can_be_stored_with_every_field_empty(session: Session) -> None:
    opp = Opportunity()
    session.add(opp)
    session.commit()
    session.refresh(opp)
    uuid.UUID(opp.id)
    for field in (
        "title",
        "opportunity_type",
        "organizer",
        "start_date",
        "end_date",
        "registration_deadline",
        "submission_deadline",
        "location",
        "mode",
        "eligibility",
        "skills_required",
        "compensation",
        "application_url",
    ):
        assert getattr(opp, field) is None, field
    assert opp.sources == []
    assert opp.evidence == []
    assert opp.created_at.tzinfo is not None


def test_opportunity_round_trips_all_fields(session: Session) -> None:
    start = datetime(2030, 1, 10, 9, 0, tzinfo=UTC)
    opp = Opportunity(
        title="Synthetic Test Opportunity",
        opportunity_type=OpportunityType.HACKATHON,
        organizer="Synthetic Org",
        start_date=start,
        end_date=start + timedelta(days=1),
        registration_deadline=start - timedelta(days=5),
        submission_deadline=start + timedelta(hours=20),
        location="Test Location",
        mode=ParticipationMode.HYBRID,
        eligibility="Students only",
        skills_required="Python, React",
        compensation="Grand Prize: $5000",
        application_url="https://example.test/apply",
    )
    session.add(opp)
    session.commit()
    session.expire_all()
    loaded = session.get(Opportunity, opp.id)
    assert loaded is not None
    assert loaded.title == "Synthetic Test Opportunity"
    assert loaded.opportunity_type is OpportunityType.HACKATHON
    assert loaded.mode is ParticipationMode.HYBRID
    assert loaded.start_date == start
    assert loaded.end_date == start + timedelta(days=1)
    assert loaded.compensation == "Grand Prize: $5000"


def test_timezone_is_normalised_to_utc(session: Session) -> None:
    ist = timezone(timedelta(hours=5, minutes=30))
    moment = datetime(2030, 3, 1, 10, 0, tzinfo=ist)
    opp = Opportunity(start_date=moment)
    session.add(opp)
    session.commit()
    session.expire_all()
    loaded = session.get(Opportunity, opp.id)
    assert loaded is not None and loaded.start_date is not None
    assert loaded.start_date == moment
    assert loaded.start_date.utcoffset() == timedelta(0)


def test_naive_datetimes_are_rejected(session: Session) -> None:
    session.add(Opportunity(start_date=datetime(2030, 1, 1, 9, 0)))
    with pytest.raises(Exception, match="Naive datetime"):
        session.commit()


def test_updated_at_changes_on_update(session: Session) -> None:
    opp = Opportunity(title="initial")
    session.add(opp)
    session.commit()
    first = opp.updated_at
    opp.title = "updated"
    session.commit()
    assert opp.updated_at > first
    assert opp.created_at <= opp.updated_at


def test_invalid_mode_is_rejected_by_database(session: Session) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO opportunities (id, mode, created_at, updated_at) "
                "VALUES ('bad', 'sideways', '2030-01-01 00:00:00', '2030-01-01 00:00:00')"
            )
        )
        session.commit()


def test_invalid_opportunity_type_is_rejected_by_database(session: Session) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO opportunities (id, opportunity_type, created_at, updated_at) "
                "VALUES ('bad', 'invalid_type', '2030-01-01 00:00:00', '2030-01-01 00:00:00')"
            )
        )
        session.commit()


# ---------------------------------------------------------------------------
# SourceReference & Opportunity relationship tests
# ---------------------------------------------------------------------------


def test_sources_relationship_and_ordering(session: Session) -> None:
    opp = Opportunity(title="e")
    opp.sources.append(
        SourceReference(source_type=SourceType.OPPORTUNITY_LISTING, url="https://a.test")
    )
    opp.sources.append(
        SourceReference(source_type=SourceType.ORGANIZER_WEBSITE, url="https://b.test")
    )
    session.add(opp)
    session.commit()
    session.expire_all()
    loaded = session.get(Opportunity, opp.id)
    assert loaded is not None
    assert {s.url for s in loaded.sources} == {"https://a.test", "https://b.test"}
    assert all(s.opportunity is loaded for s in loaded.sources)
    assert all(s.opportunity_id == loaded.id for s in loaded.sources)


def test_source_requires_existing_opportunity(session: Session) -> None:
    session.add(
        SourceReference(
            opportunity_id="does-not-exist", source_type=SourceType.OTHER, url="https://x.test"
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_opportunity_cascades_to_sources(session: Session) -> None:
    opp = Opportunity()
    opp.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://a.test"))
    session.add(opp)
    session.commit()
    session.delete(opp)
    session.commit()
    assert session.scalar(select(func.count()).select_from(SourceReference)) == 0


def test_same_url_cannot_repeat_for_one_opportunity_but_can_for_another(
    session: Session,
) -> None:
    first, second = Opportunity(), Opportunity()
    first.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://dup.test"))
    second.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://dup.test"))
    session.add_all([first, second])
    session.commit()  # allowed across opportunities

    first.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://dup.test"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_sources_without_url_are_allowed_repeatedly(session: Session) -> None:
    opp = Opportunity()
    opp.sources.append(SourceReference(source_type=SourceType.MANUAL_TEXT))
    opp.sources.append(SourceReference(source_type=SourceType.MANUAL_TEXT))
    session.add(opp)
    session.commit()
    assert len(opp.sources) == 2


def test_source_metadata_json_and_retrieval_fields(session: Session) -> None:
    when = datetime(2030, 5, 5, 12, 0, tzinfo=UTC)
    opp = Opportunity()
    opp.sources.append(
        SourceReference(
            source_type=SourceType.DOCUMENT,
            url="https://doc.test/a.pdf",
            retrieved_at=when,
            content_hash="a" * 64,
            source_metadata={"http_status": 200, "nested": {"k": [1, 2]}},
        )
    )
    session.add(opp)
    session.commit()
    session.expire_all()
    src = session.scalars(select(SourceReference)).one()
    assert src.retrieved_at == when
    assert src.source_metadata == {"http_status": 200, "nested": {"k": [1, 2]}}
    assert src.source_type is SourceType.DOCUMENT


def test_source_type_is_required(session: Session) -> None:
    opp = Opportunity()
    session.add(opp)
    session.flush()
    session.add(SourceReference(opportunity_id=opp.id, url="https://x.test"))  # type: ignore[call-arg]
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# FieldEvidence model tests
# ---------------------------------------------------------------------------


def test_field_evidence_creation_and_relationships(session: Session) -> None:
    opp = Opportunity(title="Hackathon")
    source = SourceReference(source_type=SourceType.ORGANIZER_WEBSITE, url="https://hack.test")
    opp.sources.append(source)
    session.add(opp)
    session.commit()

    evidence = FieldEvidence(
        opportunity_id=opp.id,
        source_id=source.id,
        field_name="registration_deadline",
        extracted_value="2030-05-01T23:59:59Z",
        supporting_excerpt="Registration closes May 1st at midnight UTC",
        extraction_method=ExtractionMethod.RULE_BASED,
        evidence_status=EvidenceStatus.FOUND,
    )
    session.add(evidence)
    session.commit()
    session.expire_all()

    loaded = session.get(FieldEvidence, evidence.id)
    assert loaded is not None
    assert loaded.field_name == "registration_deadline"
    assert loaded.extraction_method is ExtractionMethod.RULE_BASED
    assert loaded.evidence_status is EvidenceStatus.FOUND
    assert loaded.opportunity.id == opp.id
    assert loaded.source is not None and loaded.source.id == source.id


def test_field_evidence_cascades_on_opportunity_delete(session: Session) -> None:
    opp = Opportunity(title="Fellowship")
    session.add(opp)
    session.flush()

    evidence = FieldEvidence(
        opportunity_id=opp.id,
        field_name="title",
        extracted_value="Fellowship",
        extraction_method=ExtractionMethod.MANUAL,
        evidence_status=EvidenceStatus.FOUND,
    )
    session.add(evidence)
    session.commit()

    session.delete(opp)
    session.commit()
    assert session.scalar(select(func.count()).select_from(FieldEvidence)) == 0


def test_field_evidence_source_deletion_sets_null(session: Session) -> None:
    opp = Opportunity(title="Conference")
    source = SourceReference(source_type=SourceType.ANNOUNCEMENT, url="https://conf.test")
    opp.sources.append(source)
    session.add(opp)
    session.commit()

    evidence = FieldEvidence(
        opportunity_id=opp.id,
        source_id=source.id,
        field_name="location",
        extracted_value="San Francisco, CA",
        extraction_method=ExtractionMethod.LLM,
        evidence_status=EvidenceStatus.NEEDS_VERIFICATION,
    )
    session.add(evidence)
    session.commit()

    session.delete(source)
    session.commit()
    session.expire_all()

    loaded = session.get(FieldEvidence, evidence.id)
    assert loaded is not None
    assert loaded.source_id is None
    assert loaded.source is None


# ---------------------------------------------------------------------------
# StudentProfile and AlumniProfile tests
# ---------------------------------------------------------------------------


def test_student_profile_defaults_to_private(session: Session) -> None:
    student = StudentProfile(
        display_name="Alice Smith",
        skills="Python, SQL",
        interests="Machine Learning, Open Source",
        career_goals="Become an ML Researcher",
    )
    session.add(student)
    session.commit()
    session.refresh(student)

    assert student.visibility is StudentProfileVisibility.PRIVATE
    assert student.skills == "Python, SQL"


def test_alumni_profile_willing_to_connect_defaults_to_false(session: Session) -> None:
    alumni = AlumniProfile(
        display_name="Bob Jones",
        professional_domain="Software Engineering",
        industry="Cloud Infrastructure",
        years_experience=8,
    )
    session.add(alumni)
    session.commit()
    session.refresh(alumni)

    assert alumni.willing_to_connect is False
    assert alumni.visibility is AlumniProfileVisibility.PRIVATE


# ---------------------------------------------------------------------------
# MatchExplanation and ConnectionRequest tests
# ---------------------------------------------------------------------------


def test_match_explanation_persistence(session: Session) -> None:
    student = StudentProfile(display_name="Carol")
    opp = Opportunity(title="Summer Research")
    session.add_all([student, opp])
    session.commit()

    explanation = MatchExplanation(
        student_profile_id=student.id,
        matched_entity_type=MatchedEntityType.OPPORTUNITY,
        matched_entity_id=opp.id,
        score=0.85,
        reasons=["Interest matches Machine Learning", "Location preference matches Remote"],
        contributing_attributes={"student_skills": ["Python"], "opp_mode": "online"},
        uncertainty_notes="Eligibility criteria could not be confirmed from official listing",
        scorer_version="v1.0.0",
    )
    session.add(explanation)
    session.commit()
    session.refresh(explanation)

    assert explanation.score == 0.85
    assert len(explanation.reasons) == 2
    assert explanation.matched_entity_type is MatchedEntityType.OPPORTUNITY
    assert explanation.scorer_version == "v1.0.0"


def test_connection_request_persistence_and_status(session: Session) -> None:
    student = StudentProfile(display_name="Dave")
    alumni = AlumniProfile(
        display_name="Eve",
        professional_domain="Data Science",
        willing_to_connect=True,
    )
    session.add_all([student, alumni])
    session.commit()

    req = ConnectionRequest(
        requester_profile_id=student.id,
        recipient_profile_id=alumni.id,
        purpose=ConnectionPurpose.CAREER_GUIDANCE,
        message="I'd love to ask about transitioning into Data Science.",
    )
    session.add(req)
    session.commit()
    session.refresh(req)

    assert req.status is RequestStatus.PENDING
    assert req.purpose is ConnectionPurpose.CAREER_GUIDANCE
    assert req.responded_at is None

    # Recipient accepts
    now_utc = datetime.now(UTC)
    req.status = RequestStatus.ACCEPTED
    req.responded_at = now_utc
    session.commit()
    session.refresh(req)

    assert req.status is RequestStatus.ACCEPTED
    assert req.responded_at is not None
