"""A6 (hashing off the event loop), B2 (72-byte password limit), B3 (no account enumeration)."""

import asyncio
import importlib
import json

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.api.auth import utils
from app.schemas.admin import AdminCreate
from app.schemas.donor import DonorCreate
from app.services.otp_service import PURPOSE_ADMIN_RESET, PURPOSE_DONOR_RESET, store_otp
from tests.helpers import insert_admin, insert_donor, registration_payload

# `app.api.auth.router` as a dotted path resolves to the APIRouter the package re-exports; we need the module.
auth_router = importlib.import_module("app.api.auth.router")

DONOR_LOGIN = "/api/v1/auth/donor/login"
ADMIN_LOGIN = "/api/v1/auth/admin/login"
DONOR_CONFIRM = "/api/v1/auth/donor/password-reset/confirm"
ADMIN_CONFIRM = "/api/v1/auth/admin/password-reset/confirm"
DONOR_REQUEST = "/api/v1/auth/donor/password-reset/request"
ADMIN_REQUEST = "/api/v1/auth/admin/password-reset/request"


def _on_event_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


@pytest.fixture
def bcrypt_calls(monkeypatch):
    """Record every real bcrypt hash/verify and whether it ran on the event-loop thread."""
    calls: list[tuple[str, bool]] = []
    real_hash, real_verify = utils.bcrypt.hashpw, utils.bcrypt.checkpw

    def hash_(*a, **k):
        calls.append(("hash", _on_event_loop()))
        return real_hash(*a, **k)

    def verify_(*a, **k):
        calls.append(("verify", _on_event_loop()))
        return real_verify(*a, **k)

    monkeypatch.setattr(utils.bcrypt, "hashpw", hash_)
    monkeypatch.setattr(utils.bcrypt, "checkpw", verify_)
    return calls


def _assert_all_off_loop(calls, expected_kind):
    kinds = [kind for kind, _ in calls]
    assert expected_kind in kinds, f"expected a bcrypt {expected_kind} call, saw {kinds}"
    assert not any(on_loop for _, on_loop in calls), "bcrypt ran on the event-loop thread and blocks every request"


# ------------------------------------------------------------------ A6: off the event loop

@pytest.mark.asyncio
async def test_hashing_does_not_block_the_event_loop():
    ticks = 0

    async def ticker():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.005)
            ticks += 1

    task = asyncio.create_task(ticker())
    await utils.hash_password_async("Secret123")
    await utils.verify_password_async("Secret123", utils.hash_password("Secret123"))
    task.cancel()
    assert ticks >= 10, "the loop made no progress while bcrypt ran"


@pytest.mark.asyncio
async def test_async_wrappers_keep_behavior():
    hashed = await utils.hash_password_async("Secret123")
    assert hashed.startswith("$2")
    assert await utils.verify_password_async("Secret123", hashed) is True
    assert await utils.verify_password_async("Wrong123", hashed) is False


@pytest.mark.asyncio
async def test_donor_login_verifies_off_loop(client: AsyncClient, test_session, bcrypt_calls):
    await insert_donor(test_session)
    bcrypt_calls.clear()
    r = await client.post(DONOR_LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})
    assert r.status_code == 200
    _assert_all_off_loop(bcrypt_calls, "verify")


@pytest.mark.asyncio
async def test_admin_login_verifies_off_loop(client: AsyncClient, test_session, bcrypt_calls):
    await insert_admin(test_session)
    bcrypt_calls.clear()
    r = await client.post(ADMIN_LOGIN, json={"email": "admin1@example.com", "password": "Secret123"})
    assert r.status_code == 200
    _assert_all_off_loop(bcrypt_calls, "verify")


@pytest.mark.asyncio
async def test_donor_registration_hashes_off_loop(client: AsyncClient, bcrypt_calls, verified_registration):
    r = await verified_registration(client, registration_payload("new@example.com"))
    assert r.status_code == 201, r.text
    _assert_all_off_loop(bcrypt_calls, "hash")


@pytest.mark.asyncio
async def test_password_resets_hash_off_loop(client: AsyncClient, test_session, bcrypt_calls):
    await insert_donor(test_session)
    await insert_admin(test_session)
    await store_otp(test_session, "donor1@example.com", "123456", PURPOSE_DONOR_RESET)
    await store_otp(test_session, "admin1@example.com", "123456", PURPOSE_ADMIN_RESET)
    bcrypt_calls.clear()
    for url, email in ((DONOR_CONFIRM, "donor1@example.com"), (ADMIN_CONFIRM, "admin1@example.com")):
        r = await client.post(url, json={"email": email, "otp": "123456", "new_password": "NewSecret456"})
        assert r.status_code == 200, r.text
    _assert_all_off_loop(bcrypt_calls, "hash")


# ------------------------------------------------------------------ B2: 72-byte limit

EMOJI_100_BYTES = "A1" + "\U0001F600" * 24 + "bcdefg"  # 32 chars, 2 + 96 + 6 = 104 bytes
AT_LIMIT = "Aa1" + "x" * 69  # exactly 72 bytes
OVER_LIMIT = "Aa1" + "x" * 70  # 73 bytes, 73 characters


def _donor_create(password):
    return DonorCreate(**registration_payload("a@example.com", password))


def _admin_create(password):
    return AdminCreate(
        email="a@example.com", password=password, username="Admin", vec_registration_number="V1",
        date_of_birth="1990-01-01", mobile_number="9000000001", invite_otp="123456",
    )


@pytest.mark.parametrize("build", [_donor_create, _admin_create])
def test_registration_schemas_count_bytes_not_characters(build):
    assert build(AT_LIMIT).password == AT_LIMIT
    for bad in (OVER_LIMIT, EMOJI_100_BYTES):
        with pytest.raises(ValidationError, match="72 bytes"):
            build(bad)


@pytest.mark.asyncio
async def test_register_rejects_a_password_bcrypt_would_truncate(client: AsyncClient):
    r = await client.post("/api/v1/donors/register", json=registration_payload("long@example.com", OVER_LIMIT))
    assert r.status_code == 422
    assert "72 bytes" in r.text


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [DONOR_CONFIRM, ADMIN_CONFIRM])
async def test_reset_confirm_enforces_the_password_policy(client: AsyncClient, url):
    base = {"email": "someone@example.com", "otp": "123456"}
    for password, needle in (
        (OVER_LIMIT, "72 bytes"), (EMOJI_100_BYTES, "72 bytes"),
        ("a", "at least 8"), ("alllowercase1", "uppercase"), ("NoDigitsHere", "digit"),
    ):
        r = await client.post(url, json={**base, "new_password": password})
        assert r.status_code == 422, (password, r.text)
        assert needle in r.text, (password, r.text)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [DONOR_LOGIN, ADMIN_LOGIN])
async def test_login_rejects_an_overlong_password_clearly(client: AsyncClient, url):
    r = await client.post(url, json={"email": "someone@example.com", "password": OVER_LIMIT})
    assert r.status_code == 422
    assert "72 bytes" in r.text


# ------------------------------------------------------------------ B3: enumeration

@pytest.mark.asyncio
@pytest.mark.parametrize("login_url,make", [(DONOR_LOGIN, insert_donor), (ADMIN_LOGIN, insert_admin)])
async def test_login_does_the_same_bcrypt_work_for_unknown_and_known_accounts(
    client: AsyncClient, test_session, bcrypt_calls, login_url, make,
):
    await make(test_session)
    known_email = "donor1@example.com" if login_url == DONOR_LOGIN else "admin1@example.com"
    bcrypt_calls.clear()

    known = await client.post(login_url, json={"email": known_email, "password": "Wrong123"})
    known_work = list(bcrypt_calls)
    bcrypt_calls.clear()
    unknown = await client.post(login_url, json={"email": "ghost@example.com", "password": "Wrong123"})
    unknown_work = list(bcrypt_calls)

    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json()
    assert [k for k, _ in unknown_work] == [k for k, _ in known_work] == ["verify"], (
        "an unknown email must still pay for one bcrypt verify, or response time reveals which emails exist"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("url,make,email", [
    (DONOR_CONFIRM, insert_donor, "donor1@example.com"),
    (ADMIN_CONFIRM, insert_admin, "admin1@example.com"),
])
async def test_reset_confirm_answers_identically_for_known_and_unknown_emails(
    client: AsyncClient, test_session, url, make, email,
):
    await make(test_session)
    body = {"otp": "000000", "new_password": "NewSecret456"}

    known = await client.post(url, json={**body, "email": email})
    unknown = await client.post(url, json={**body, "email": "ghost@example.com"})

    assert known.status_code == unknown.status_code == 400
    assert known.json() == unknown.json() == {"detail": "Invalid or expired code"}


class _Mailer:
    def __init__(self):
        self.sent: list[str] = []

    async def send_otp_email(self, email, otp, name):
        self.sent.append(email)
        return True


@pytest.mark.asyncio
@pytest.mark.parametrize("url,make,email", [
    (DONOR_REQUEST, insert_donor, "donor1@example.com"),
    (ADMIN_REQUEST, insert_admin, "admin1@example.com"),
])
async def test_reset_request_is_identical_and_sends_mail_after_the_response(
    client: AsyncClient, test_session, monkeypatch, url, make, email,
):
    await make(test_session)
    mailer = _Mailer()
    monkeypatch.setattr(auth_router, "get_email_service", lambda: mailer)

    known = await client.post(url, json={"email": email})
    unknown = await client.post(url, json={"email": "ghost@example.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert mailer.sent == [email], "only the real account gets a code"


@pytest.mark.asyncio
async def test_known_email_does_not_wait_for_smtp(client: AsyncClient, test_session, monkeypatch):
    """The response must be complete before the mail is sent, so SMTP latency cannot reveal a real account.

    httpx's ASGITransport only returns after the whole app call (background tasks included), so this drives
    the ASGI app directly and watches when the response finishes versus when the mailer returns.
    """
    from app.main import app

    await insert_donor(test_session)
    release = asyncio.Event()

    class SlowMailer:
        async def send_otp_email(self, email, otp, name):
            await release.wait()
            return True

    monkeypatch.setattr(auth_router, "get_email_service", lambda: SlowMailer())

    body = json.dumps({"email": "donor1@example.com"}).encode()
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST", "scheme": "http",
        "path": DONOR_REQUEST, "raw_path": DONOR_REQUEST.encode(), "query_string": b"",
        "headers": [(b"host", b"test"), (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode())],
        "client": ("127.0.0.1", 1234), "server": ("test", 80),
    }
    response_finished = asyncio.Event()
    sent_request = False

    async def receive():
        nonlocal sent_request
        if not sent_request:
            sent_request = True
            return {"type": "http.request", "body": body, "more_body": False}
        await release.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.body" and not message.get("more_body"):
            response_finished.set()

    call = asyncio.create_task(app(scope, receive, send))
    try:
        await asyncio.wait_for(response_finished.wait(), timeout=3)
        assert not call.done(), "the mail task should still be running after the response"
    finally:
        release.set()
        await call
