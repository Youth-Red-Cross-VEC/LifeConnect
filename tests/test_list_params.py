"""P3-64/P3-65: every list endpoint is explicitly bounded and uses the same parameter names."""

import pytest
from httpx import AsyncClient

from app.api.auth.utils import create_access_token
from tests.helpers import insert_donor, insert_request

BASE = "/api/v1/blood-requests"


@pytest.mark.asyncio
@pytest.mark.parametrize("path,status", [
    ("pending", "Pending"), ("ongoing", "Approved"), ("closed", "Closed"),
    ("expired", "Expired"), ("declined", "Declined"),
])
async def test_request_lists_accept_limit_and_offset(admin_client: AsyncClient, test_session, path, status):
    for n in (1, 2, 3):
        await insert_request(test_session, n, status=status)
    everything = (await admin_client.get(f"{BASE}/{path}")).json()
    assert len(everything) == 3
    first_two = (await admin_client.get(f"{BASE}/{path}", params={"limit": 2})).json()
    assert len(first_two) == 2
    rest = (await admin_client.get(f"{BASE}/{path}", params={"limit": 2, "offset": 2})).json()
    assert len(rest) == 1
    assert {r["id"] for r in first_two} | {r["id"] for r in rest} == {r["id"] for r in everything}


@pytest.mark.asyncio
async def test_pending_list_is_no_longer_silently_capped_at_50(admin_client: AsyncClient, test_session):
    for n in range(1, 56):
        await insert_request(test_session, n, status="Pending")
    assert len((await admin_client.get(f"{BASE}/pending")).json()) == 55


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["pending", "ongoing"])
async def test_limit_is_validated(admin_client: AsyncClient, path):
    assert (await admin_client.get(f"{BASE}/{path}", params={"limit": 0})).status_code == 422
    assert (await admin_client.get(f"{BASE}/{path}", params={"limit": 501})).status_code == 422
    assert (await admin_client.get(f"{BASE}/{path}", params={"offset": -1})).status_code == 422


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
    for n in range(3):
        await client.post("/api/v1/queries/", json={
            "user_name": "D", "user_email": "donor1@example.com", "user_query": f"My question number {n}",
        })
    headers = {"Authorization": f"Bearer {token}"}
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
