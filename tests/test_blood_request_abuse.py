"""A5: the public blood-request form is rate limited, optionally CAPTCHA-protected, and notifies admins once."""

import importlib
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.config import Settings, get_settings
from app.services.email_service import EmailService
from tests.helpers import insert_admin, insert_request

auth_router = importlib.import_module("app.api.auth.router")
email_service = importlib.import_module("app.services.email_service")

URL = "/api/v1/blood-requests/"


async def _hospital(session):
    await insert_request(session, 1)  # also creates HOSP-1


def _body(**extra) -> dict:
    return {
        "patient_name": "Sample Patient", "blood_group": "O+", "hospital_id": "HOSP-1",
        "contact_number": "9000200001", "patient_age": 40,
        "due_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        "units_required": 2, **extra,
    }


# ------------------------------------------------------------------ dedicated rate limit

def test_dedicated_limit_is_stricter_than_the_default():
    settings = get_settings()
    assert settings.BLOOD_REQUEST_RATE_LIMIT == Settings.model_fields["BLOOD_REQUEST_RATE_LIMIT"].default
    first = int(settings.BLOOD_REQUEST_RATE_LIMIT.split("/")[0])
    assert first < settings.RATE_LIMIT_PER_MINUTE


@pytest.mark.asyncio
async def test_form_is_throttled_per_client(client: AsyncClient, test_session):
    await _hospital(test_session)
    per_minute = int(get_settings().BLOOD_REQUEST_RATE_LIMIT.split("/")[0])

    codes = [(await client.post(URL, json=_body())).status_code for _ in range(per_minute + 2)]

    assert codes[:per_minute] == [201] * per_minute
    assert set(codes[per_minute:]) == {429}


# ------------------------------------------------------------------ optional reCAPTCHA

@pytest.fixture
def enforced(monkeypatch):
    monkeypatch.setattr(get_settings(), "RECAPTCHA_ENFORCED", True)


def _stub_verify(monkeypatch, result: bool):
    calls = []

    async def fake(token, action=None):
        calls.append((token, action))
        return result

    monkeypatch.setattr(auth_router, "verify_recaptcha", fake)
    return calls


@pytest.mark.asyncio
async def test_not_enforced_by_default(client: AsyncClient, test_session):
    await _hospital(test_session)
    assert get_settings().RECAPTCHA_ENFORCED is False
    assert (await client.post(URL, json=_body())).status_code == 201


@pytest.mark.asyncio
async def test_enforced_rejects_a_missing_or_bad_token(client: AsyncClient, test_session, enforced, monkeypatch):
    await _hospital(test_session)
    calls = _stub_verify(monkeypatch, False)

    assert (await client.post(URL, json=_body())).status_code == 400
    assert calls == []  # no token: never even asks Google
    assert (await client.post(URL, json=_body(recaptcha_token="bad"))).status_code == 400


@pytest.mark.asyncio
async def test_enforced_accepts_a_valid_token_for_the_right_action(
    client: AsyncClient, test_session, enforced, monkeypatch,
):
    await _hospital(test_session)
    calls = _stub_verify(monkeypatch, True)

    response = await client.post(URL, json=_body(recaptcha_token="good"))

    assert response.status_code == 201
    assert calls == [("good", "blood_request")]
    assert "recaptcha_token" not in response.json()


# ------------------------------------------------------------------ one notification, capped

class _SmtpSpy:
    def __init__(self):
        self.sent = []

    async def connect(self):
        return None

    async def login(self, username, password):
        return None

    async def send_message(self, message, **kwargs):
        self.sent.append((message, kwargs))

    async def quit(self):
        return None


@pytest.fixture
def smtp(monkeypatch):
    spy = _SmtpSpy()
    monkeypatch.setattr(email_service.aiosmtplib, "SMTP", lambda **kwargs: spy)
    return spy


@pytest.mark.asyncio
async def test_one_email_goes_to_all_admins_via_bcc(client: AsyncClient, test_session, smtp):
    await _hospital(test_session)
    for n in (1, 2, 3):
        await insert_admin(test_session, n)

    assert (await client.post(URL, json=_body())).status_code == 201

    assert len(smtp.sent) == 1, "one SMTP session per submission, however many admins there are"
    message, kwargs = smtp.sent[0]
    assert set(kwargs["recipients"][1:]) == {f"admin{n}@example.com" for n in (1, 2, 3)}
    assert kwargs["recipients"][0] == get_settings().MAIL_FROM
    # Admins must not see each other: nobody but the sender appears in a header.
    assert "admin1@example.com" not in message.as_string().split("\n\n", 1)[0]
    assert message["To"] == get_settings().MAIL_FROM
    assert message["Bcc"] is None


@pytest.mark.asyncio
async def test_recipient_list_is_capped(client: AsyncClient, test_session, smtp, monkeypatch):
    monkeypatch.setattr(get_settings(), "ADMIN_NOTIFY_MAX_RECIPIENTS", 3)
    await _hospital(test_session)
    for n in range(1, 8):
        await insert_admin(test_session, n)

    assert (await client.post(URL, json=_body())).status_code == 201

    assert len(smtp.sent) == 1
    assert len(smtp.sent[0][1]["recipients"]) - 1 == 3


@pytest.mark.asyncio
async def test_no_notification_without_active_admins(client: AsyncClient, test_session, smtp):
    await _hospital(test_session)
    await insert_admin(test_session, 1, active=False)

    assert (await client.post(URL, json=_body())).status_code == 201

    assert smtp.sent == []


@pytest.mark.asyncio
async def test_notification_sends_each_address_once(smtp):
    service = EmailService(get_settings())
    await service.notify_admins_new_request(["a@example.com", "a@example.com", "b@example.com"], {})
    assert smtp.sent[0][1]["recipients"][1:] == ["a@example.com", "b@example.com"]
