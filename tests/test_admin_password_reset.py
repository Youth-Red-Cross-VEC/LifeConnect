"""Administrator reset authorization and transaction regression tests."""

import importlib
from datetime import timedelta

import pytest
from sqlalchemy import update

from app.core.request_status import AdminRole, AdminStatus
from app.models.otp import OtpCode
from app.services.otp_service import PURPOSE_ADMIN_RESET, PURPOSE_DONOR_RESET, store_otp
from app.utils.dates import utcnow
from tests.helpers import cookie_headers, insert_admin, insert_donor, refresh_cookie

auth_router = importlib.import_module("app.api.auth.router")
RESET = "/api/v1/auth/admin/password-reset"
LOGIN = "/api/v1/auth/admin/login"
PROFILE = "/api/v1/admins/me/profile"
EMAIL = "admin1@example.com"
BODY = {"email": EMAIL, "otp": "123456", "new_password": "Replacement123"}


async def test_admin_reset_revokes_sessions_without_changing_role(client, test_session, monkeypatch):
    admin = await insert_admin(test_session, 1, role=AdminRole.ADMIN)
    sent = []

    async def capture_code(email, otp, name):
        sent.append((email, otp))

    monkeypatch.setattr(auth_router, "_send_reset_email", capture_code)
    login = await client.post(LOGIN, json={"email": EMAIL, "password": "Secret123"})
    assert login.status_code == 200
    old_cookie = refresh_cookie(login)
    old_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get(PROFILE, headers=old_headers)).status_code == 200

    known = await client.post(f"{RESET}/request", json={"email": EMAIL.upper()})
    unknown = await client.post(f"{RESET}/request", json={"email": "unknown@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    [(address, code)] = sent
    assert address == EMAIL

    payload = {**BODY, "email": EMAIL.upper(), "otp": code}
    unexpected = {**payload, "role": "super_admin", "active_status": "Inactive"}
    assert (await client.post(f"{RESET}/confirm", json=unexpected)).status_code == 422
    confirmed = await client.post(f"{RESET}/confirm", json=payload)
    assert confirmed.status_code == 200
    assert set(confirmed.json()) == {"message"}
    replay = await client.post(f"{RESET}/confirm", json=payload)
    assert replay.status_code == 400
    assert (await client.post("/api/v1/auth/refresh", headers=cookie_headers(old_cookie))).status_code == 401
    assert (await client.get(PROFILE, headers=old_headers)).status_code == 401
    assert (await client.post(LOGIN, json={"email": EMAIL, "password": "Secret123"})).status_code == 401
    fresh = await client.post(LOGIN, json={"email": EMAIL, "password": BODY["new_password"]})
    assert fresh.status_code == 200
    fresh_headers = {"Authorization": f"Bearer {fresh.json()['access_token']}"}
    assert (await client.get(PROFILE, headers=fresh_headers)).status_code == 200
    assert (await client.post("/api/v1/admins/invite", headers=fresh_headers,
                              json={"email": "invitee@example.com"})).status_code == 403
    await test_session.refresh(admin)
    assert admin.role == AdminRole.ADMIN
    assert admin.active_status == AdminStatus.ACTIVE


async def test_donor_and_admin_codes_cannot_cross_roles_at_the_same_email(client, test_session):
    await insert_admin(test_session, 1)
    await insert_donor(test_session, email=EMAIL)
    await store_otp(test_session, EMAIL, BODY["otp"], PURPOSE_DONOR_RESET)
    await store_otp(test_session, EMAIL, "654321", PURPOSE_ADMIN_RESET)
    donor_confirm = "/api/v1/auth/donor/password-reset/confirm"

    assert (await client.post(f"{RESET}/confirm", json=BODY)).status_code == 400
    assert (await client.post(donor_confirm, json={**BODY, "otp": "654321"})).status_code == 400
    assert (await client.post(f"{RESET}/confirm", json={**BODY, "otp": "654321"})).status_code == 200
    assert (await client.post(donor_confirm, json=BODY)).status_code == 200


async def test_expired_wrong_and_unknown_codes_share_the_same_error(client, test_session):
    await insert_admin(test_session, 1)
    await store_otp(test_session, EMAIL, BODY["otp"], PURPOSE_ADMIN_RESET)
    wrong = await client.post(f"{RESET}/confirm", json={**BODY, "otp": "000000"})
    await test_session.execute(update(OtpCode).where(OtpCode.purpose == PURPOSE_ADMIN_RESET).values(
        expires_at=utcnow() - timedelta(seconds=1),
    ))
    await test_session.commit()
    expired = await client.post(f"{RESET}/confirm", json=BODY)
    unknown = await client.post(f"{RESET}/confirm", json={**BODY, "email": "unknown@example.com"})
    for response in (wrong, expired, unknown):
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid or expired code"}


async def test_failed_admin_password_update_does_not_spend_code(client, test_session, monkeypatch):
    await insert_admin(test_session, 1, role=AdminRole.SUPER_ADMIN)
    await store_otp(test_session, EMAIL, BODY["otp"], PURPOSE_ADMIN_RESET)

    async def fail_hash(password):
        raise RuntimeError("Synthetic failure")

    with monkeypatch.context() as patch:
        patch.setattr(auth_router, "hash_password_async", fail_hash)
        assert (await client.post(f"{RESET}/confirm", json=BODY)).status_code == 500
    assert (await client.post(f"{RESET}/confirm", json=BODY)).status_code == 200
    fresh = await client.post(LOGIN, json={"email": EMAIL, "password": BODY["new_password"]})
    assert fresh.status_code == 200
    profile = await client.get(PROFILE, headers={"Authorization": f"Bearer {fresh.json()['access_token']}"})
    assert profile.json()["role"] == AdminRole.SUPER_ADMIN


@pytest.mark.parametrize("payload", [
    {"otp": "123456"},
    {**BODY, "new_password": "Private!"},
    {**BODY, "otp": {"code": "private-otp"}},
])
async def test_bad_admin_payload_does_not_echo_submitted_values(client, payload):
    response = await client.post(f"{RESET}/confirm", json=payload)
    assert response.status_code == 422
    for secret in ("123456", "Private!", "private-otp"):
        assert secret not in response.text
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
