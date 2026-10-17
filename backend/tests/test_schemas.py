from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import Event, EventMode, SourceReference, SourceType
from app.schemas import EventCreate, EventRead, SourceReferenceCreate

NOW = datetime(2030, 1, 1, tzinfo=UTC)


def test_empty_event_is_valid() -> None:
    assert EventCreate().sources == []


def test_valid_event_with_sources() -> None:
    e = EventCreate(
        event_name="n",
        mode="online",
        start_date=NOW,
        end_date=NOW + timedelta(days=1),
        registration_url="https://example.test/r",
        sources=[{"source_type": "event_listing", "url": "https://example.test"}],
    )
    assert e.mode is EventMode.ONLINE


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
        EventCreate(registration_url=url)
    with pytest.raises(ValidationError):
        SourceReferenceCreate(source_type=SourceType.OTHER, url=url)


def test_end_before_start_is_rejected() -> None:
    with pytest.raises(ValidationError, match="end_date"):
        EventCreate(start_date=NOW, end_date=NOW - timedelta(hours=1))


@pytest.mark.parametrize(
    "field", ["start_date", "end_date", "registration_deadline", "submission_deadline"]
)
def test_naive_datetimes_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError, match="timezone"):
        EventCreate(**{field: datetime(2030, 1, 1)})


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EventCreate(mode="sideways")  # type: ignore[arg-type]


def test_source_needs_url_unless_manual_text() -> None:
    with pytest.raises(ValidationError, match="url is required"):
        SourceReferenceCreate(source_type=SourceType.EVENT_LISTING)
    assert SourceReferenceCreate(source_type=SourceType.MANUAL_TEXT).url is None


def test_event_read_is_built_from_orm_without_exposing_extras(session) -> None:  # type: ignore[no-untyped-def]
    event = Event(event_name="n")
    event.sources.append(SourceReference(source_type=SourceType.OTHER, url="https://a.test"))
    session.add(event)
    session.commit()
    data = EventRead.model_validate(event).model_dump()
    assert data["event_name"] == "n"
    assert data["sources"][0]["url"] == "https://a.test"
    assert "_sa_instance_state" not in data
