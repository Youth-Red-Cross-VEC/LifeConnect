"""Regression guards for controls the audit found sound: they must not quietly weaken.

JWT algorithm pinning, HTML-escaping of everything that reaches an email, and the admin audit trail.
"""

import base64
import inspect
import json
from datetime import datetime, timedelta

import pytest
from fastapi.routing import APIRoute
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import select

from app.api.auth import utils
from app.api.auth.deps import get_current_admin
from app.config import get_settings
from app.main import app
from app.models.audit import AdminAuditLog
from app.services import email_service as email_module
from app.services.email_service import EmailService
from tests.helpers import insert_donor

# ------------------------------------------------------------------ JWT: algorithm and key are server-pinned

CLAIMS = {"sub": "DON-1", "user_type": "donor", "email": "donor1@example.com", "type": "access"}
MINE = "/api/v1/queries/my-queries"


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def _claims(**override):
    return {**CLAIMS, "exp": datetime.utcnow() + timedelta(minutes=5), **override}


def _forged() -> dict[str, str]:
    key = utils.SECRET_KEY
    return {
        "alg none, no signature": f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(_claims(exp=9999999999))}.",
        "another HMAC algorithm, right key": jwt.encode(_claims(), key, algorithm="HS512"),
        "right algorithm, wrong key": jwt.encode(_claims(), "x" * 40, algorithm="HS256"),
        "expired": jwt.encode(_claims(exp=datetime.utcnow() - timedelta(seconds=1)), key, algorithm="HS256"),
        "tampered signature": jwt.encode(_claims(), key, algorithm="HS256")[:-4] + "AAAA",
    }


@pytest.mark.parametrize("label", list(_forged()))
def test_decode_token_rejects_forged_tokens(label):
    assert utils.decode_token(_forged()[label]) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("label", list(_forged()))
async def test_protected_routes_reject_forged_tokens(client: AsyncClient, test_session, label):
    await insert_donor(test_session)
    r = await client.get(MINE, headers={"Authorization": f"Bearer {_forged()[label]}"})
    assert r.status_code == 401, label


@pytest.mark.asyncio
async def test_a_correctly_signed_token_is_accepted(client: AsyncClient, test_session):
    await insert_donor(test_session)
    good = jwt.encode(_claims(), utils.SECRET_KEY, algorithm=utils.ALGORITHM)
    assert (await client.get(MINE, headers={"Authorization": f"Bearer {good}"})).status_code == 200


@pytest.mark.asyncio
async def test_an_access_token_cannot_be_used_to_refresh(client: AsyncClient, test_session):
    await insert_donor(test_session)
    access = utils.create_access_token({"sub": "DON-1", "user_type": "donor", "email": "donor1@example.com"})
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401


# ------------------------------------------------------------------ email: user data is escaped in every template

PAYLOAD = '<script>alert("x")</script><img src=x onerror=alert(1)>'


@pytest.fixture
def sent_html(monkeypatch):
    """Capture the HTML body of every message instead of sending it."""
    bodies: list[str] = []

    async def capture(message, **kwargs):
        for part in message.walk():
            if part.get_content_type() == "text/html":
                bodies.append(part.get_payload(decode=True).decode("utf-8"))

    monkeypatch.setattr(email_module.aiosmtplib, "send", capture)
    return bodies


def _assert_inert(html: str):
    assert "<script>" not in html and "<img src=x" not in html, "user-supplied markup reached the email unescaped"
    assert "&lt;script&gt;" in html


@pytest.mark.asyncio
async def test_new_request_notification_escapes_every_field(sent_html):
    details = {k: PAYLOAD for k in ("patient_name", "blood_group", "hospital_name", "units_required", "due_date")}
    await EmailService(get_settings()).notify_admins_new_request(["a@example.com"], details)
    _assert_inert(sent_html[0])


@pytest.mark.asyncio
async def test_donor_notification_escapes_every_field(sent_html):
    await EmailService(get_settings()).send_blood_request_notification(
        donor_email="d@example.com", donor_name=PAYLOAD, blood_group=PAYLOAD, patient_name=PAYLOAD,
        hospital_name=PAYLOAD, hospital_address=PAYLOAD, contact_number=PAYLOAD, due_date=PAYLOAD,
        attendant_name=PAYLOAD, units_required=PAYLOAD, request_reason=PAYLOAD, patient_age=PAYLOAD,
    )
    _assert_inert(sent_html[0])


@pytest.mark.asyncio
async def test_otp_and_certificate_mails_escape_the_name(sent_html, tmp_path):
    service = EmailService(get_settings())
    certificate = tmp_path / "Asha_20261005_120000_certificate.png"
    certificate.write_bytes(b"png")
    await service.send_otp_email("d@example.com", "123456", PAYLOAD)
    await service.send_certificate_email("d@example.com", PAYLOAD, certificate)
    assert len(sent_html) == 2
    for html in sent_html:
        _assert_inert(html)


def test_every_html_template_value_is_escaped_at_the_source():
    """Cheap tripwire: no f-string template in the mail service interpolates a bare name into HTML."""
    source = inspect.getsource(EmailService)
    assert "_esc(" in source
    for risky in ("{donor_name}", "{name}", "{patient_name}"):
        if risky in source:
            # every use must sit in a function that escapes its arguments first
            for func in (EmailService.send_blood_request_notification, EmailService.send_otp_email,
                         EmailService.send_certificate_email):
                body = inspect.getsource(func)
                if risky in body:
                    assert "_esc(" in body, f"{func.__name__} interpolates {risky} without escaping"


# ------------------------------------------------------------------ the admin audit trail

WRITES = {"POST", "PUT", "PATCH", "DELETE"}


def _admin_write_routes():
    # Walk the feature routers directly: FastAPI wraps included routers in an internal object, so
    # app.routes no longer lists their endpoints.
    from app.api.v1 import admins, analytics, blood_requests, certificates, donors, hospitals, queries

    for module in (admins, analytics, blood_requests, certificates, donors, hospitals, queries):
        for route in module.router.routes:
            if not isinstance(route, APIRoute) or not WRITES & route.methods:
                continue
            if any(dep.call is get_current_admin for dep in route.dependant.dependencies):
                yield route


def test_there_are_admin_write_routes_to_check():
    assert len(list(_admin_write_routes())) >= 15


@pytest.mark.parametrize("route", list(_admin_write_routes()), ids=lambda r: f"{sorted(r.methods)[0]} {r.path}")
def test_every_admin_write_route_records_an_audit_entry(route):
    assert "record_admin_action" in inspect.getsource(route.endpoint), (
        f"{route.path} changes state as an admin but writes no audit row"
    )


def test_no_route_exposes_the_audit_log_for_editing_or_deleting():
    exposed = [path for path in app.openapi()["paths"] if "audit" in path.lower()]
    assert exposed == [], "the audit trail must have no read/edit/delete API until it is designed with access control"


def test_audit_actor_is_never_a_request_field():
    """record_admin_action takes the admin id from the authenticated admin object, in every call site."""
    import re
    from pathlib import Path

    for path in (Path(__file__).resolve().parent.parent / "app" / "api" / "v1").glob("*.py"):
        for call in re.findall(r"record_admin_action\(\s*session,\s*([^,]+),", path.read_text(encoding="utf-8")):
            assert call.strip() in {"current_admin.id", "admin_id", "admin.id"} or call.strip().startswith("admin_id"), (
                f"{path.name}: audit actor {call!r} must come from the authenticated admin"
            )


@pytest.mark.asyncio
async def test_audit_rows_name_the_authenticated_admin(admin_client: AsyncClient, test_session):
    from tests.helpers import insert_request

    await insert_request(test_session, 1, status="Pending")
    assert (await admin_client.post("/api/v1/blood-requests/REQ-1/decline")).status_code == 200
    rows = (await test_session.execute(select(AdminAuditLog))).scalars().all()
    assert [r.admin_id for r in rows] == ["ADM-test123"]
