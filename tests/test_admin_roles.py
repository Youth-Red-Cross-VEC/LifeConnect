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


async def test_invite_remains_retryable_after_registration_conflict(client, test_session):
    from app.services.otp_service import PURPOSE_ADMIN_INVITE, store_otp
    from tests.helpers import insert_admin

    existing = await insert_admin(test_session, 1)
    email = "invited@example.com"
    await store_otp(test_session, email, "123456", PURPOSE_ADMIN_INVITE)
    body = dict(email=email, password="Invitation123", username="Invited",
                vec_registration_number=existing.vec_registration_number,
                date_of_birth="1990-01-01", mobile_number="9000000001", invite_otp="123456")
    path = "/api/v1/admins/register"
    assert (await client.post(path, json=body)).status_code == 409
    body["vec_registration_number"] = "NEW-2"
    assert (await client.post(path, json=body)).status_code == 201
    assert (await client.post(path, json=body)).status_code == 400

async def test_previous_admin_session_cannot_inherit_promotion(admin_client, test_session):
    from tests.helpers import cookie_headers, refresh_cookie

    headers, account = await _normal_headers(test_session)
    login = await admin_client.post("/api/v1/auth/admin/login", json={"email": account.email, "password": "Secret123"})
    assert login.status_code == 200
    cookie = refresh_cookie(login)
    assert (await admin_client.put(f"/api/v1/admins/{account.id}", json={"role": "super_admin"})).status_code == 200
    assert (await admin_client.get("/api/v1/admins/me/profile", headers=headers)).status_code == 401
    assert (await admin_client.post("/api/v1/auth/refresh", headers=cookie_headers(cookie))).status_code == 401

async def test_parallel_self_demotions_preserve_one_super_admin(postgres_security_engine):
    import asyncio
    from fastapi import HTTPException
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.api.v1.admins import update_admin
    from app.models.admin import AdminDetails
    from app.models.audit import AdminAuditLog
    from app.schemas.admin import AdminUpdate

    async with postgres_security_engine.begin() as connection:
        await connection.run_sync(AdminAuditLog.__table__.create)
    sessions = async_sessionmaker(postgres_security_engine, expire_on_commit=False)
    async with sessions() as seeding:
        first = await insert_admin(seeding, 1, role=AdminRole.SUPER_ADMIN)
        second = await insert_admin(seeding, 2, role=AdminRole.SUPER_ADMIN)
    barrier = asyncio.Barrier(2)

    async def demote(account_id):
        try:
            async with sessions.begin() as transaction:
                actor = await transaction.get(AdminDetails, account_id)
                await asyncio.wait_for(barrier.wait(), 5)
                await update_admin(account_id, AdminUpdate(role=AdminRole.ADMIN), transaction, actor)
            return 200
        except HTTPException as exc:
            return exc.status_code

    statuses = await asyncio.wait_for(asyncio.gather(demote(first.id), demote(second.id)), 10)
    assert sorted(statuses) == [200, 409]
    async with sessions() as check:
        roles = (await check.scalars(select(AdminDetails.role))).all()
        assert roles.count(AdminRole.SUPER_ADMIN) == 1
