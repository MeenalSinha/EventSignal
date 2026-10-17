from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import API_V1_PREFIX
from app.models import Opportunity, SourceReference, SourceType

OPPORTUNITIES_URL = f"{API_V1_PREFIX}/opportunities"
EVENTS_COMPAT_URL = f"{API_V1_PREFIX}/events"


@pytest.mark.parametrize("url", [OPPORTUNITIES_URL, EVENTS_COMPAT_URL])
def test_fresh_database_lists_no_opportunities(client: TestClient, url: str) -> None:
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


@pytest.mark.parametrize("url", [OPPORTUNITIES_URL, EVENTS_COMPAT_URL])
def test_stored_opportunities_are_listed_with_sources_and_paginated(
    client: TestClient, session: Session, url: str
) -> None:
    for index in range(3):
        opp = Opportunity(title=f"synthetic-{index}")
        opp.sources.append(
            SourceReference(source_type=SourceType.OTHER, url=f"https://s{index}.test")
        )
        session.add(opp)
    session.commit()

    body = client.get(url, params={"limit": 2}).json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["sources"][0]["url"].startswith("https://s")

    second = client.get(url, params={"limit": 2, "offset": 2}).json()
    assert len(second["items"]) == 1
    seen = {i["id"] for i in body["items"]} | {i["id"] for i in second["items"]}
    assert len(seen) == 3


@pytest.mark.parametrize("url", [OPPORTUNITIES_URL, EVENTS_COMPAT_URL])
def test_invalid_pagination_is_rejected(client: TestClient, url: str) -> None:
    assert client.get(url, params={"limit": 0}).status_code == 422
    assert client.get(url, params={"limit": 1000}).status_code == 422
    assert client.get(url, params={"offset": -1}).status_code == 422


@pytest.mark.parametrize("url", [OPPORTUNITIES_URL, EVENTS_COMPAT_URL])
def test_no_write_methods_exist(client: TestClient, url: str) -> None:
    assert client.post(url, json={}).status_code == 405
    assert client.delete(url).status_code == 405
