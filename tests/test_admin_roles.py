import pytest
from httpx import AsyncClient

from app.api.auth.utils import create_access_token
from app.core.request_status import AdminRole
from app.services.email_service import EmailService
from tests.helpers import insert_admin


async def _normal_headers(test_session):
    admin = await insert_admin(test_session, 40, role=AdminRole.ADMIN, email="normal@example.com")
    token = create_access_token({
        "sub": admin.id,
        "email": admin.email,
        "user_type": "admin",
        "tv": admin.token_version,
    })
    return {"Authorization": f"Bearer {token}"}, admin


@pytest.mark.asyncio
async def test_normal_admin_cannot_invite_or_change_other_admin(client: AsyncClient, test_session):
    headers, _ = await _normal_headers(test_session)
    other = await insert_admin(test_session, 41)
    invite = await client.post("/api/v1/admins/invite", json={"email": "new@example.com"}, headers=headers)
    edit = await client.put(f"/api/v1/admins/{other.id}", json={"username": "Changed"}, headers=headers)
    assert invite.status_code == 403
    assert edit.status_code == 403


@pytest.mark.asyncio
async def test_normal_admin_cannot_activate_deactivate_or_change_roles(client: AsyncClient, test_session):
    headers, own = await _normal_headers(test_session)
    other = await insert_admin(test_session, 42, active=False)
    deactivate = await client.patch(f"/api/v1/admins/{other.id}/deactivate", headers=headers)
    activate = await client.patch(f"/api/v1/admins/{other.id}/activate", headers=headers)
    role = await client.put(f"/api/v1/admins/{own.id}", json={"role": "super_admin"}, headers=headers)
    assert [deactivate.status_code, activate.status_code, role.status_code] == [403, 403, 403]


@pytest.mark.asyncio
async def test_normal_admin_can_edit_only_own_name_and_mobile(client: AsyncClient, test_session):
    headers, own = await _normal_headers(test_session)
    allowed = await client.put(f"/api/v1/admins/{own.id}", json={"username": "Updated", "mobile_number": "9999999999"}, headers=headers)
    forbidden = await client.put(f"/api/v1/admins/{own.id}", json={"department": "Ops"}, headers=headers)
    assert allowed.status_code == 200
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_super_admin_can_change_role_and_last_super_admin_is_protected(admin_client: AsyncClient, test_session):
    last_super_demote = await admin_client.put("/api/v1/admins/ADM-test123", json={"role": "admin"})
    last_super_deactivate = await admin_client.patch("/api/v1/admins/ADM-test123/deactivate")
    assert last_super_demote.status_code == 409
    assert last_super_deactivate.status_code == 400

    other = await insert_admin(test_session, 43)
    changed = await admin_client.put(f"/api/v1/admins/{other.id}", json={"role": "super_admin"})
    assert changed.status_code == 200
    assert changed.json()["role"] == "super_admin"


@pytest.mark.asyncio
async def test_super_admin_can_invite_and_toggle_an_admin(admin_client: AsyncClient, test_session, monkeypatch):
    async def sent(self, email, otp, name, purpose="password_reset"):
        return True

    monkeypatch.setattr(EmailService, "send_otp_email", sent)
    invited = await admin_client.post("/api/v1/admins/invite", json={"email": "invite@example.com"})
    target = await insert_admin(test_session, 44, active=False)
    activated = await admin_client.patch(f"/api/v1/admins/{target.id}/activate")
    deactivated = await admin_client.patch(f"/api/v1/admins/{target.id}/deactivate")
    assert invited.status_code == 200
    assert activated.status_code == 200
    assert deactivated.status_code == 200
