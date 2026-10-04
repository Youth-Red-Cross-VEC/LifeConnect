"""Logs must not carry full recipient addresses or exception text that may embed PII."""

import logging
import sys

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.core.database import Database
from app.core.logging import mask_email
from app.services import email_service as email_module
from app.services.email_service import EmailService
from tests.helpers import insert_donor


def test_mask_email():
    assert mask_email("jane.doe@example.com") == "j***@example.com"
    assert mask_email("not-an-email") == "***"


@pytest.mark.asyncio
async def test_email_logs_mask_recipient(monkeypatch, caplog):
    async def ok(*a, **k):
        return None

    async def boom(*a, **k):
        raise RuntimeError("rejected jane.doe@example.com")

    svc = EmailService(get_settings())
    caplog.set_level(logging.INFO)

    monkeypatch.setattr(email_module.aiosmtplib, "send", ok)
    assert await svc.send_email("jane.doe@example.com", "s", "<p>x</p>")
    monkeypatch.setattr(email_module.aiosmtplib, "send", boom)
    assert not await svc.send_email("jane.doe@example.com", "s", "<p>x</p>")

    assert "jane.doe@example.com" not in caplog.text
    assert "j***@example.com" in caplog.text


@pytest.mark.asyncio
async def test_login_error_log_omits_exception_text(client: AsyncClient, test_session, monkeypatch, caplog):
    await insert_donor(test_session)

    def boom(*a, **k):
        raise RuntimeError("leak: donor1@example.com 9000000001")

    monkeypatch.setattr(sys.modules["app.api.auth.router"], "verify_password", boom)
    caplog.set_level(logging.INFO)
    r = await client.post("/api/v1/auth/donor/login", json={"email": "donor1@example.com", "password": "x"})
    assert r.status_code == 500
    bad = [
        r.getMessage() for r in caplog.records
        if r.name.startswith("app.") and ("leak:" in r.getMessage() or "9000000001" in r.getMessage())
    ]
    assert not bad, bad


def test_engine_hides_statement_parameters():
    database = Database("postgresql://u:p@localhost/db")
    assert database.engine.sync_engine.hide_parameters is True
