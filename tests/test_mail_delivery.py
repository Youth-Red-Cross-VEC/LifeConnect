"""Delivery decisions are based on relay acceptance, including partial or missing acknowledgements."""
import asyncio
from email import policy
from email.parser import BytesParser
from unittest.mock import AsyncMock

import aiosmtplib
import pytest

from app.config import get_settings
from app.services.email_service import EmailService


async def test_connect_retry_then_acceptance(monkeypatch):
    relay = AsyncMock(side_effect=[aiosmtplib.SMTPConnectError("unreachable"), ({}, "accepted")])
    monkeypatch.setattr(aiosmtplib, "send", relay)
    service = EmailService(get_settings())
    assert await service.send_otp_email("synthetic@example.com", "012345", "Donor", "donor_enrollment")
    assert relay.await_count == 2
    assert "registration" in relay.await_args.args[0]["Subject"]


@pytest.mark.parametrize("result", [aiosmtplib.SMTPReadTimeoutError("unknown"),
                                    ({"other@example.com": (550, "refused")}, "partial")])
async def test_no_replay_after_submission(monkeypatch, result):
    relay = AsyncMock(side_effect=[result])
    monkeypatch.setattr(aiosmtplib, "send", relay)
    assert not await EmailService(get_settings()).send_email(
        "synthetic@example.com", "Notice", "body", bcc=["other@example.com"]
    )
    relay.assert_awaited_once()


async def test_invalid_envelope_or_attachment_never_submitted(monkeypatch, tmp_path):
    relay = AsyncMock()
    monkeypatch.setattr(aiosmtplib, "send", relay)
    service = EmailService(get_settings())
    assert not await service.send_email("one@example.com", "Notice", "body", bcc=["bad\naddress"])
    assert not await service.send_certificate_email("one@example.com", "Donor", tmp_path / "absent.txt")
    relay.assert_not_awaited()


async def test_certificate_mime_over_disposable_smtp(tmp_path):
    received = []
    async def relay(reader, writer):
        writer.write(b"220 localhost ready\r\n")
        try:
            while line := await reader.readline():
                command = line.split()[0].upper()
                if command == b"DATA":
                    writer.write(b"354 send content\r\n")
                    await writer.drain()
                    received.append(await reader.readuntil(b"\r\n.\r\n"))
                elif command == b"QUIT":
                    writer.write(b"221 closing\r\n")
                    break
                writer.write(b"250 OK\r\n")
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(relay, "127.0.0.1", 0)
    async with server:
        settings = get_settings().model_copy(update={
            "MAIL_SERVER": "127.0.0.1", "MAIL_PORT": server.sockets[0].getsockname()[1],
            "MAIL_USE_TLS": False, "MAIL_USERNAME": None, "MAIL_PASSWORD": None,
            "MAIL_FROM": "sender@example.com",
        })
        attachment = tmp_path / "certificate.txt"
        attachment.write_bytes(b"Synthetic certificate")
        assert await EmailService(settings).send_certificate_email("one@example.com", "Test", attachment)
    assert len(received) == 1
    message = BytesParser(policy=policy.default).parsebytes(received[0])
    assert message["To"] == "one@example.com"
    assert message.get_content_type() == "multipart/mixed"
    part, = message.iter_attachments()
    assert part.get_payload(decode=True) == attachment.read_bytes()

async def test_batch_partial_acceptance_and_disconnect_are_never_replayed(monkeypatch):
    client = AsyncMock()
    client.send_message.side_effect = [
        ({"declined@example.com": (550, "refused")}, "partial"),
        ({}, "accepted"),
        aiosmtplib.SMTPServerDisconnected("unknown"),
    ]
    monkeypatch.setattr(aiosmtplib, "SMTP", lambda **kwargs: client)
    messages = [{"to": "one@example.com", "subject": "Synthetic", "html_body": "body",
                 "bcc": ["declined@example.com"]},
                *[{"to": f"recipient{i}@example.com", "subject": "Synthetic", "html_body": "body"}
                  for i in range(3)]]
    assert await EmailService(get_settings()).send_many(messages) == 1
    assert client.send_message.await_count == 3
    client.quit.assert_awaited_once()

async def test_linked_certificate_is_rejected_before_dispatch(tmp_path):
    from app.services.certificate_service import CertificateService
    service = CertificateService(output_dir=str(tmp_path))
    filename = "synthetic_20261124_120000_certificate.txt"
    original = tmp_path / "source.txt"
    original.write_bytes(b"another certificate")
    (tmp_path / filename).hardlink_to(original)
    assert await service.get_certificate(filename) is None
    assert original.read_bytes() == b"another certificate"
