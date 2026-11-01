"""B7: an admin cannot lock out the admin team, and other admins' personal details are not exposed."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.auth.deps import get_current_admin
from app.main import app
from app.models.admin import AdminDetails
from app.core.request_status import AdminStatus, AdminRole
from tests.helpers import insert_admin

ME = "ADM-test123"  # the admin behind the admin_client fixture
HIDDEN = {"date_of_birth", "mobile_number"}


async def _status(session, admin_id: str) -> str:
    value = (await session.execute(select(AdminDetails.active_status).where(AdminDetails.id == admin_id))).scalar_one()
    return value.value


# ------------------------------------------------------------------ lock-out protection

@pytest.mark.asyncio
async def test_admin_cannot_deactivate_themselves(admin_client: AsyncClient, test_session):
    r = await admin_client.patch(f"/api/v1/admins/{ME}/deactivate")
    assert r.status_code == 400
    assert "own account" in r.json()["detail"]
    assert await _status(test_session, ME) == "Active"


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_themselves_through_put(admin_client: AsyncClient, test_session):
    r = await admin_client.put(f"/api/v1/admins/{ME}", json={"active_status": "Inactive"})
    assert r.status_code == 400
    assert await _status(test_session, ME) == "Active"


@pytest.mark.asyncio
async def test_self_update_of_other_fields_still_works(admin_client: AsyncClient):
    r = await admin_client.put(f"/api/v1/admins/{ME}", json={"department": "Ops", "active_status": "Active"})
    assert r.status_code == 200
    assert r.json()["department"] == "Ops"


@pytest.mark.asyncio
async def test_admin_can_still_deactivate_another_admin(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    assert (await admin_client.patch("/api/v1/admins/ADM-1/deactivate")).status_code == 200
    assert await _status(test_session, "ADM-1") == "Inactive"


@pytest.fixture
def stale_caller(test_session):
    """A caller the dependency accepts but who is not an active admin row, to reach the last-admin guard.

    Through the real dependency this cannot happen (an inactive admin cannot authenticate), but two admins
    deactivating each other at the same moment can leave exactly this state, so the guard must not rely on it.
    """
    caller = AdminDetails(id="ADM-gone", email="gone@example.com", password="x", username="Gone",
                          authentication_id="A", vec_registration_number="V", date_of_birth="1990-01-01",
                          mobile_number="1", active_status=AdminStatus.INACTIVE, role=AdminRole.SUPER_ADMIN)

    async def override():
        return caller

    app.dependency_overrides[get_current_admin] = override
    yield caller
    app.dependency_overrides.pop(get_current_admin, None)


@pytest.mark.asyncio
async def test_the_last_active_admin_cannot_be_deactivated(client: AsyncClient, test_session, stale_caller):
    only_id = (await insert_admin(test_session, 1, role=AdminRole.SUPER_ADMIN)).id

    for call in (
        client.patch(f"/api/v1/admins/{only_id}/deactivate"),
        client.put(f"/api/v1/admins/{only_id}", json={"active_status": "Inactive"}),
    ):
        r = await call
        assert r.status_code == 409, r.text
        assert "last active super admin" in r.json()["detail"]
    assert await _status(test_session, only_id) == "Active"


@pytest.mark.asyncio
async def test_deactivating_an_already_inactive_admin_is_not_blocked(client: AsyncClient, test_session, stale_caller):
    await insert_admin(test_session, 1)
    await insert_admin(test_session, 2, active=False)
    assert (await client.patch("/api/v1/admins/ADM-2/deactivate")).status_code == 200
    assert await _status(test_session, "ADM-1") == "Active"


# ------------------------------------------------------------------ personal details of other admins

@pytest.mark.asyncio
async def test_detail_of_another_admin_hides_dob_and_phone(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    body = (await admin_client.get("/api/v1/admins/ADM-1")).json()
    assert HIDDEN.isdisjoint(body)
    assert body["username"] == "Admin 1" and body["department"] == "IT"


@pytest.mark.asyncio
async def test_own_detail_keeps_the_full_record(admin_client: AsyncClient):
    for url in (f"/api/v1/admins/{ME}", "/api/v1/admins/me/profile"):
        body = (await admin_client.get(url)).json()
        assert HIDDEN <= set(body), url
        assert body["mobile_number"] == "9999999999"


@pytest.mark.asyncio
async def test_list_hides_others_but_not_the_callers_own_row(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    items = {a["id"]: a for a in (await admin_client.get("/api/v1/admins/")).json()["items"]}
    assert HIDDEN <= set(items[ME])
    assert HIDDEN.isdisjoint(items["ADM-1"])


@pytest.mark.asyncio
async def test_update_response_for_another_admin_hides_dob_and_phone(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    r = await admin_client.put("/api/v1/admins/ADM-1", json={"department": "Ops"})
    assert r.status_code == 200
    assert HIDDEN.isdisjoint(r.json())
    assert r.json()["department"] == "Ops"
