"""P3-64/P3-65: every list endpoint is explicitly bounded and uses the same parameter names."""

import pytest
from httpx import AsyncClient

from app.api.auth.utils import create_access_token
from tests.helpers import insert_donor, insert_request

BASE = "/api/v1/blood-requests"
PAGINATED = {"pending", "ongoing"}


def _items(payload, path: str) -> list:
    return payload


@pytest.mark.asyncio
@pytest.mark.parametrize("path,status", [
    ("pending", "Pending"), ("ongoing", "Approved"), ("closed", "Closed"),
    ("expired", "Expired"), ("declined", "Declined"),
])
async def test_request_lists_accept_pagination(admin_client: AsyncClient, test_session, path, status):
    for n in (1, 2, 3):
        await insert_request(test_session, n, status=status)
    everything = _items((await admin_client.get(f"{BASE}/{path}")).json(), path)
    assert len(everything) == 3
    params_first = {"page_size": 2} if path in PAGINATED else {"limit": 2}
    params_rest = {"page": 2, "page_size": 2} if path in PAGINATED else {"limit": 2, "offset": 2}
    first_two = _items((await admin_client.get(f"{BASE}/{path}", params=params_first)).json(), path)
    assert len(first_two) == 2
    rest = _items((await admin_client.get(f"{BASE}/{path}", params=params_rest)).json(), path)
    assert len(rest) == 1
    assert {r["id"] for r in first_two} | {r["id"] for r in rest} == {r["id"] for r in everything}


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["pending", "ongoing"])
async def test_paginated_request_lists_expose_the_total(admin_client: AsyncClient, test_session, path):
    for n in (1, 2, 3):
        await insert_request(test_session, n, status="Pending" if path == "pending" else "Approved")
    response = await admin_client.get(f"{BASE}/{path}", params={"page": 2, "page_size": 1})
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    body = response.json()
    assert len(body) == 1


@pytest.mark.asyncio
async def test_pending_list_reports_the_full_total_beyond_one_page(admin_client: AsyncClient, test_session):
    for n in range(1, 56):
        await insert_request(test_session, n, status="Pending")
    default_page = (await admin_client.get(f"{BASE}/pending")).json()
    assert len(default_page) == 55
    full_page = (await admin_client.get(f"{BASE}/pending", params={"page_size": 100})).json()
    assert len(full_page) == 55


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["pending", "ongoing"])
async def test_page_size_is_validated(admin_client: AsyncClient, path):
    assert (await admin_client.get(f"{BASE}/{path}", params={"page_size": 0})).status_code == 422
    assert (await admin_client.get(f"{BASE}/{path}", params={"page_size": 501})).status_code == 422
    assert (await admin_client.get(f"{BASE}/{path}", params={"page": 0})).status_code == 422


@pytest.mark.asyncio
async def test_query_lists_accept_limit_and_offset(admin_client: AsyncClient, client: AsyncClient):
    for n in range(3):
        r = await client.post("/api/v1/queries/", json={
            "user_name": "Sam", "user_email": "sam@example.com", "user_query": f"Question number {n} for admins",
        })
        assert r.status_code == 201
    assert len((await admin_client.get("/api/v1/queries/pending")).json()) == 3
    assert len((await admin_client.get("/api/v1/queries/pending", params={"limit": 2})).json()) == 2
    assert len((await admin_client.get("/api/v1/queries/pending", params={"limit": 2, "offset": 2})).json()) == 1


@pytest.mark.asyncio
async def test_my_queries_is_bounded(client: AsyncClient, test_session):
    await insert_donor(test_session)
    token = create_access_token({"sub": "DON-1", "user_type": "donor", "email": "donor1@example.com"})
    headers = {"Authorization": f"Bearer {token}"}
    for n in range(3):  # filed while signed in, so the donor owns them
        await client.post("/api/v1/queries/", json={
            "user_name": "D", "user_email": "donor1@example.com", "user_query": f"My question number {n}",
        }, headers=headers)
    assert len((await client.get("/api/v1/queries/my-queries", headers=headers)).json()) == 3
    page = await client.get("/api/v1/queries/my-queries", params={"limit": 2}, headers=headers)
    assert len(page.json()) == 2
    assert (await client.get("/api/v1/queries/my-queries", params={"limit": 0}, headers=headers)).status_code == 422


@pytest.mark.asyncio
async def test_donor_search_uses_canonical_name_and_keeps_the_old_alias(admin_client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    for param in ("search", "name_search"):
        r = await admin_client.get("/api/v1/donors/", params={param: "Donor2"})
        assert r.status_code == 200
        assert [d["id"] for d in r.json()["items"]] == ["DON-2"], param


@pytest.mark.asyncio
async def test_query_status_filter_uses_canonical_name_and_keeps_the_old_alias(admin_client: AsyncClient, client: AsyncClient):
    await client.post("/api/v1/queries/", json={
        "user_name": "Sam", "user_email": "sam@example.com", "user_query": "A pending question here",
    })
    for param in ("status", "status_filter"):
        assert (await admin_client.get("/api/v1/queries/", params={param: "pending"})).json()["total"] == 1, param
        assert (await admin_client.get("/api/v1/queries/", params={param: "resolved"})).json()["total"] == 0, param
