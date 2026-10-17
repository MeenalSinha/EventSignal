"""Model behaviour. Rows here are explicit synthetic fixtures living only in the isolated
test database; nothing in the application ever creates them."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Event, EventMode, SourceReference, SourceType


def test_event_can_be_stored_with_every_field_empty(session: Session) -> None:
    event = Event()
    session.add(event)
    session.commit()
    session.refresh(event)
    uuid.UUID(event.id)
    for field in (
        "event_name",
        "organizer",
        "start_date",
        "end_date",
        "registration_deadline",
        "submission_deadline",
        "venue",
        "mode",
        "eligibility",
        "participation_fee",
        "agenda",
        "prizes_and_benefits",
        "registration_url",
    ):
        assert getattr(event, field) is None, field
    assert event.sources == []
    assert event.created_at.tzinfo is not None


def test_event_round_trips_all_fields(session: Session) -> None:
    start = datetime(2030, 1, 10, 9, 0, tzinfo=UTC)
    event = Event(
        event_name="Synthetic Test Event",
        organizer="Synthetic Org",
        start_date=start,
        end_date=start + timedelta(days=1),
        registration_deadline=start - timedelta(days=5),
        submission_deadline=start + timedelta(hours=20),
        venue="Test Venue",
        mode=EventMode.HYBRID,
        eligibility="text",
        participation_fee="text",
        agenda="text",
        prizes_and_benefits="text",
        registration_url="https://example.test/register",
    )
    session.add(event)
    session.commit()
    session.expire_all()
    loaded = session.get(Event, event.id)
    assert loaded is not None
    assert loaded.mode is EventMode.HYBRID
    assert loaded.start_date == start
    assert loaded.end_date == start + timedelta(days=1)


def test_timezone_is_normalised_to_utc(session: Session) -> None:
    ist = timezone(timedelta(hours=5, minutes=30))
    moment = datetime(2030, 3, 1, 10, 0, tzinfo=ist)
    event = Event(start_date=moment)
    session.add(event)
    session.commit()
    session.expire_all()
    loaded = session.get(Event, event.id)
    assert loaded is not None and loaded.start_date is not None
    assert loaded.start_date == moment
    assert loaded.start_date.utcoffset() == timedelta(0)


def test_naive_datetimes_are_rejected(session: Session) -> None:
    session.add(Event(start_date=datetime(2030, 1, 1, 9, 0)))
    with pytest.raises(Exception, match="Naive datetime"):
        session.commit()


def test_updated_at_changes_on_update(session: Session) -> None:
    event = Event(event_name="a")
    session.add(event)
    session.commit()
    first = event.updated_at
    event.event_name = "b"
    session.commit()
    assert event.updated_at > first
    assert event.created_at <= event.updated_at


def test_invalid_mode_is_rejected_by_database(session: Session) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO events (id, mode, created_at, updated_at) "
                "VALUES ('bad', 'sideways', '2030-01-01 00:00:00', '2030-01-01 00:00:00')"
            )
        )
        session.commit()


def test_sources_relationship_and_ordering(session: Session) -> None:
    event = Event(event_name="e")
    event.sources.append(
        SourceReference(source_type=SourceType.EVENT_LISTING, url="https://a.test")
    )
    event.sources.append(
        SourceReference(source_type=SourceType.ORGANIZER_WEBSITE, url="https://b.test")
    )
    session.add(event)
    session.commit()
    session.expire_all()
    loaded = session.get(Event, event.id)
    assert loaded is not None
    assert {s.url for s in loaded.sources} == {"https://a.test", "https://b.test"}
    assert all(s.event is loaded for s in loaded.sources)
    assert all(s.event_id == loaded.id for s in loaded.sources)


def test_source_requires_existing_event(session: Session) -> None:
    session.add(
        SourceReference(
            event_id="does-not-exist", source_type=SourceType.OTHER, url="https://x.test"
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_event_cascades_to_sources(session: Session) -> None:
    event = Event()
    event.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://a.test"))
    session.add(event)
    session.commit()
    session.delete(event)
    session.commit()
    assert session.scalar(select(func.count()).select_from(SourceReference)) == 0


def test_same_url_cannot_repeat_for_one_event_but_can_for_another(session: Session) -> None:
    first, second = Event(), Event()
    first.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://dup.test"))
    second.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://dup.test"))
    session.add_all([first, second])
    session.commit()  # allowed across events

    first.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://dup.test"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_sources_without_url_are_allowed_repeatedly(session: Session) -> None:
    event = Event()
    event.sources.append(SourceReference(source_type=SourceType.MANUAL_TEXT))
    event.sources.append(SourceReference(source_type=SourceType.MANUAL_TEXT))
    session.add(event)
    session.commit()
    assert len(event.sources) == 2


def test_source_metadata_json_and_retrieval_fields(session: Session) -> None:
    when = datetime(2030, 5, 5, 12, 0, tzinfo=UTC)
    event = Event()
    event.sources.append(
        SourceReference(
            source_type=SourceType.DOCUMENT,
            url="https://doc.test/a.pdf",
            retrieved_at=when,
            content_hash="a" * 64,
            source_metadata={"http_status": 200, "nested": {"k": [1, 2]}},
        )
    )
    session.add(event)
    session.commit()
    session.expire_all()
    src = session.scalars(select(SourceReference)).one()
    assert src.retrieved_at == when
    assert src.source_metadata == {"http_status": 200, "nested": {"k": [1, 2]}}
    assert src.source_type is SourceType.DOCUMENT


def test_source_type_is_required(session: Session) -> None:
    event = Event()
    session.add(event)
    session.flush()
    session.add(SourceReference(event_id=event.id, url="https://x.test"))  # type: ignore[call-arg]
    with pytest.raises(IntegrityError):
        session.commit()
