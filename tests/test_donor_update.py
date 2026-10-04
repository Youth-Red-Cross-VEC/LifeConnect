"""PATCH /donors/{id} must persist every field its schema advertises (P1-17)."""

import pytest
from httpx import AsyncClient

from app.api.auth.utils import create_access_token
from tests.helpers import insert_donor


def donor_headers(donor_id: str, email: str) -> dict:
    token = create_access_token({"sub": donor_id, "user_type": "donor", "email": email})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_patch_persists_contact_and_address_fields(client: AsyncClient, test_session):
    donor = await insert_donor(test_session, 1)
    headers = donor_headers(donor.id, donor.email)

    response = await client.patch(
        f"/api/v1/donors/{donor.id}",
        headers=headers,
        json={
            "name": "New Name",
            "contact_number": "9111111111",
            "address": "99 New Street",
            "city": "Madurai",
            "state": "Tamil Nadu",
            "pincode": "625001",
        },
    )
    assert response.status_code == 200, response.text

    fetched = (await client.get(f"/api/v1/donors/{donor.id}", headers=headers)).json()
    assert fetched["name"] == "New Name"
    assert fetched["personal_details"]["contact_number"] == "9111111111"
    assert fetched["address"]["address"] == "99 New Street"
    assert fetched["address"]["city"] == "Madurai"
    assert fetched["address"]["state"] == "Tamil Nadu"
    assert fetched["address"]["pincode"] == "625001"


@pytest.mark.asyncio
async def test_patch_leaves_omitted_fields_unchanged(client: AsyncClient, test_session):
    donor = await insert_donor(test_session, 1)
    headers = donor_headers(donor.id, donor.email)

    await client.patch(f"/api/v1/donors/{donor.id}", headers=headers, json={"city": "Salem"})
    fetched = (await client.get(f"/api/v1/donors/{donor.id}", headers=headers)).json()
    assert fetched["address"]["city"] == "Salem"
    assert fetched["address"]["address"] == "1 Test Street"
    assert fetched["personal_details"]["contact_number"] == "9000000001"


@pytest.mark.asyncio
async def test_patch_rejects_invalid_values(client: AsyncClient, test_session):
    donor = await insert_donor(test_session, 1)
    headers = donor_headers(donor.id, donor.email)
    assert (await client.patch(f"/api/v1/donors/{donor.id}", headers=headers, json={"contact_number": "abc"})).status_code == 422
    assert (await client.patch(f"/api/v1/donors/{donor.id}", headers=headers, json={"blood_group": "Z+"})).status_code == 422


@pytest.mark.asyncio
async def test_patch_other_donor_is_forbidden(client: AsyncClient, test_session):
    a = await insert_donor(test_session, 1)
    b = await insert_donor(test_session, 2)
    response = await client.patch(
        f"/api/v1/donors/{b.id}", headers=donor_headers(a.id, a.email), json={"city": "X"}
    )
    assert response.status_code == 403
