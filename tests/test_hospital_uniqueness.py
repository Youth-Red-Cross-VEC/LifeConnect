"""P2-41: a hospital is identified by name + branch + pincode, not name alone."""

import pytest
from httpx import AsyncClient

BASE = {
    "hospital_name": "City Care Hospital", "hospital_address": "12 Main Road", "pincode": "600001",
    "city": "Chennai", "state": "Tamil Nadu", "country": "India",
}


async def _create(client, **over):
    return await client.post("/api/v1/hospitals/", json={**BASE, **over})


@pytest.mark.asyncio
async def test_same_name_different_branch_is_allowed(admin_client: AsyncClient):
    assert (await _create(admin_client, branch="North")).status_code == 201
    assert (await _create(admin_client, branch="South")).status_code == 201


@pytest.mark.asyncio
async def test_same_name_different_pincode_is_allowed(admin_client: AsyncClient):
    assert (await _create(admin_client)).status_code == 201
    assert (await _create(admin_client, pincode="600002")).status_code == 201


@pytest.mark.asyncio
async def test_same_name_branch_pincode_is_rejected_case_insensitively(admin_client: AsyncClient):
    assert (await _create(admin_client, branch="North")).status_code == 201
    dup = await _create(admin_client, hospital_name="city care hospital", branch="NORTH")
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_duplicate_without_branch_is_rejected(admin_client: AsyncClient):
    assert (await _create(admin_client)).status_code == 201
    assert (await _create(admin_client)).status_code == 409


@pytest.mark.asyncio
async def test_update_cannot_create_a_duplicate(admin_client: AsyncClient):
    await _create(admin_client, branch="North")
    south = (await _create(admin_client, branch="South")).json()
    r = await admin_client.patch(f"/api/v1/hospitals/{south['id']}", json={"branch": "North"})
    assert r.status_code == 409
    ok = await admin_client.patch(f"/api/v1/hospitals/{south['id']}", json={"landmark": "Near park"})
    assert ok.status_code == 200
