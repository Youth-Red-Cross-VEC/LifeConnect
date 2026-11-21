"""Exercise the donor reset through the same public endpoints as the browser."""

import importlib
from datetime import timedelta

import pytest
from sqlalchemy import update

from app.models.otp import OtpCode
from app.services.otp_service import PURPOSE_ADMIN_RESET, PURPOSE_DONOR_RESET, store_otp
from app.utils.dates import utcnow
from tests.helpers import cookie_headers, insert_donor, refresh_cookie

auth_router = importlib.import_module("app.api.auth.router")
RESET = "/api/v1/auth/donor/password-reset"
LOGIN = "/api/v1/auth/donor/login"
EMAIL = "donor1@example.com"
BODY = {"email": EMAIL, "otp": "123456", "new_password": "Replacement123"}


async def test_reset_from_delivered_code_revokes_sessions_and_rejects_replay(client, test_session, monkeypatch):
    await insert_donor(test_session)
    sent = []

    async def capture_code(email, otp, name):
        sent.append((email, otp))

    monkeypatch.setattr(auth_router, "_send_reset_email", capture_code)
    login = await client.post(LOGIN, json={"email": EMAIL, "password": "Secret123"})
    assert login.status_code == 200
    old_cookie = refresh_cookie(login)
    old_access = login.json()["access_token"]

    known = await client.post(f"{RESET}/request", json={"email": EMAIL.upper()})
    unknown = await client.post(f"{RESET}/request", json={"email": "unknown@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    [(address, code)] = sent
    assert address == EMAIL

    payload = {**BODY, "email": EMAIL.upper(), "otp": code}
    assert (await client.post(f"{RESET}/confirm", json=payload)).status_code == 200
    assert (await client.post(f"{RESET}/confirm", json=payload)).status_code == 400
    assert (await client.post("/api/v1/auth/refresh", headers=cookie_headers(old_cookie))).status_code == 401
    assert (await client.get("/api/v1/donors/DON-1", headers={"Authorization": f"Bearer {old_access}"})).status_code == 401
    assert (await client.post(LOGIN, json={"email": EMAIL, "password": "Secret123"})).status_code == 401
    assert (await client.post(LOGIN, json={"email": EMAIL, "password": BODY["new_password"]})).status_code == 200


async def test_expired_and_other_purpose_codes_are_rejected(client, test_session):
    await insert_donor(test_session)
    await store_otp(test_session, EMAIL, BODY["otp"], PURPOSE_ADMIN_RESET)
    wrong_purpose = await client.post(f"{RESET}/confirm", json=BODY)
    await store_otp(test_session, EMAIL, BODY["otp"], PURPOSE_DONOR_RESET)
    await test_session.execute(update(OtpCode).where(OtpCode.purpose == PURPOSE_DONOR_RESET).values(
        expires_at=utcnow() - timedelta(seconds=1),
    ))
    await test_session.commit()
    expired = await client.post(f"{RESET}/confirm", json=BODY)
    assert wrong_purpose.status_code == expired.status_code == 400
    assert wrong_purpose.json() == expired.json() == {"detail": "Invalid or expired code"}


async def test_failed_password_update_does_not_spend_code(client, test_session, monkeypatch):
    await insert_donor(test_session)
    await store_otp(test_session, EMAIL, BODY["otp"], PURPOSE_DONOR_RESET)

    async def fail_hash(password):
        raise RuntimeError("Synthetic failure")

    with monkeypatch.context() as patch:
        patch.setattr(auth_router, "hash_password_async", fail_hash)
        assert (await client.post(f"{RESET}/confirm", json=BODY)).status_code == 500
    assert (await client.post(f"{RESET}/confirm", json=BODY)).status_code == 200


@pytest.mark.parametrize("changes", [{"new_password": "Private!"}, {"otp": {"code": "private-otp"}}])
async def test_bad_payload_does_not_echo_submitted_values(client, changes):
    response = await client.post(f"{RESET}/confirm", json={**BODY, **changes})
    assert response.status_code == 422
    assert "Private!" not in response.text
    assert "private-otp" not in response.text
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
