"""A2: support-query ownership follows the authenticated donor, never an unverified email string."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.query import QueryTable
from tests.helpers import insert_donor, registration_payload

QUERIES = "/api/v1/queries/"
MINE = "/api/v1/queries/my-queries"
LOGIN = "/api/v1/auth/donor/login"

PAYLOAD = {"user_name": "Visitor", "user_email": "victim@example.com", "user_query": "How do I update my phone number?"}


async def _donor_headers(client: AsyncClient, email: str) -> dict:
    r = await client.post(LOGIN, json={"email": email, "password": "Secret123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_registering_with_a_victims_email_does_not_expose_their_queries(admin_client: AsyncClient, verified_registration):
    # The victim (no donor account) submits an anonymous query and an admin answers it.
    created = await admin_client.post(QUERIES, json=PAYLOAD)
    assert created.status_code == 201, created.text
    query_id = created.json()["id"]
    reply = await admin_client.post(f"{QUERIES}{query_id}/reply", json={"admin_response": "Private answer"})
    assert reply.status_code == 200

    # A later verified registration using that email must still not inherit the anonymous query.
    reg = await verified_registration(admin_client, registration_payload("victim@example.com"))
    assert reg.status_code == 201, reg.text
    headers = await _donor_headers(admin_client, "victim@example.com")

    mine = await admin_client.get(MINE, headers=headers)
    assert mine.status_code == 200
    assert mine.json() == [], "an anonymous query must not become visible to whoever registers its email"


@pytest.mark.asyncio
async def test_donor_sees_only_queries_they_submitted_while_signed_in(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    h1 = await _donor_headers(client, "donor1@example.com")
    h2 = await _donor_headers(client, "donor2@example.com")

    sent = await client.post(QUERIES, json={**PAYLOAD, "user_email": "donor1@example.com"}, headers=h1)
    assert sent.status_code == 201

    row = (await test_session.execute(select(QueryTable))).scalar_one()
    assert row.donor_id == "DON-1"
    assert [q["id"] for q in (await client.get(MINE, headers=h1)).json()] == [row.id]
    assert (await client.get(MINE, headers=h2)).json() == []


@pytest.mark.asyncio
async def test_claiming_someone_elses_email_does_not_leak_to_that_email_owner(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    h1 = await _donor_headers(client, "donor1@example.com")
    h2 = await _donor_headers(client, "donor2@example.com")

    # Donor 1 files a query that lists donor 2's email as the contact address.
    await client.post(QUERIES, json={**PAYLOAD, "user_email": "donor2@example.com"}, headers=h1)

    assert (await client.get(MINE, headers=h2)).json() == []
    assert len((await client.get(MINE, headers=h1)).json()) == 1


@pytest.mark.asyncio
async def test_anonymous_and_legacy_queries_are_admin_only(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await client.post(QUERIES, json={**PAYLOAD, "user_email": "donor1@example.com"})  # anonymous
    h1 = await _donor_headers(client, "donor1@example.com")

    assert (await client.get(MINE, headers=h1)).json() == []
    row = (await test_session.execute(select(QueryTable))).scalar_one()
    assert row.donor_id is None


@pytest.mark.asyncio
async def test_admin_has_no_donor_queries(admin_client: AsyncClient):
    await admin_client.post(QUERIES, json={**PAYLOAD, "user_email": "testadmin@example.com"})
    assert (await admin_client.get(MINE)).json() == []


@pytest.mark.asyncio
async def test_stale_or_invalid_token_on_submit_is_treated_as_anonymous(client: AsyncClient, test_session):
    r = await client.post(QUERIES, json=PAYLOAD, headers={"Authorization": "Bearer not-a-token"})
    assert r.status_code == 201
    assert (await test_session.execute(select(QueryTable))).scalar_one().donor_id is None


@pytest.mark.asyncio
async def test_my_queries_still_requires_authentication(client: AsyncClient):
    assert (await client.get(MINE)).status_code == 401


# ------------------------------------------------------------------ what a non-admin gets to see

@pytest.mark.asyncio
async def test_submitter_and_donor_views_do_not_expose_the_admin_id(admin_client: AsyncClient, client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    headers = await _donor_headers(client, "donor1@example.com")
    created = await client.post(QUERIES, json={**PAYLOAD, "user_email": "donor1@example.com"}, headers=headers)
    assert created.status_code == 201
    assert "admin_id" not in created.json(), "the anonymous/donor submit response must not carry the internal admin id"

    reply = await admin_client.post(f"{QUERIES}{created.json()['id']}/reply", json={"admin_response": "Done"})
    assert reply.status_code == 200 and reply.json()["admin_id"] == "ADM-test123"  # admins still see it

    mine = (await client.get(MINE, headers=headers)).json()
    assert mine[0]["admin_response"] == "Done"
    assert "admin_id" not in mine[0]
    assert mine[0]["admin_name"] == "Test Admin"  # who answered is still shown, by name
