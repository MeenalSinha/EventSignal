from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import API_V1_PREFIX
from app.models import Event, SourceReference, SourceType

URL = f"{API_V1_PREFIX}/events"


def test_fresh_database_lists_no_events(client: TestClient) -> None:
    resp = client.get(URL)
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_stored_events_are_listed_with_sources_and_paginated(
    client: TestClient, session: Session
) -> None:
    for index in range(3):
        event = Event(event_name=f"synthetic-{index}")
        event.sources.append(
            SourceReference(source_type=SourceType.OTHER, url=f"https://s{index}.test")
        )
        session.add(event)
    session.commit()

    body = client.get(URL, params={"limit": 2}).json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["sources"][0]["url"].startswith("https://s")

    second = client.get(URL, params={"limit": 2, "offset": 2}).json()
    assert len(second["items"]) == 1
    seen = {i["id"] for i in body["items"]} | {i["id"] for i in second["items"]}
    assert len(seen) == 3


def test_invalid_pagination_is_rejected(client: TestClient) -> None:
    assert client.get(URL, params={"limit": 0}).status_code == 422
    assert client.get(URL, params={"limit": 1000}).status_code == 422
    assert client.get(URL, params={"offset": -1}).status_code == 422


def test_no_write_methods_exist(client: TestClient) -> None:
    assert client.post(URL, json={}).status_code == 405
    assert client.delete(URL).status_code == 405
