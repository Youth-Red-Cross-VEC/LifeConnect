"""B14: certificate filenames, placeholder encoding, attachment headers and same-second collisions."""

import asyncio
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import pytest

from app.config import get_settings
from app.services import certificate_service as cs
from app.services.certificate_service import CertificateService
from app.services.email_service import EmailService


@pytest.fixture
def service(tmp_path):
    output = tmp_path / "certs"
    output.mkdir()
    return CertificateService(template_dir=str(tmp_path / "templates"), output_dir=str(output))


class _Clock:
    """datetime stand-in whose now() is frozen, so two certificates land in the same second."""

    @staticmethod
    def now():
        return datetime(2026, 10, 5, 12, 0, 0)


# ------------------------------------------------------------------ filename validation

def test_a_trailing_newline_is_not_a_valid_filename(service):
    good = "Asha_20261005_120000_certificate.png"
    (service.output_dir / good).write_bytes(b"png")

    assert service._resolve_safe(good) is not None
    for bad in (good + "\n", good + "\r\n", good + " ", "\n" + good, good + "\x00"):
        assert service._resolve_safe(bad) is None, repr(bad)


def test_non_ascii_digits_are_not_valid_in_the_timestamp(service):
    assert service._resolve_safe("Asha_Ù¢Ù Ù¢Ù¦Ù¡Ù Ù Ù¥_120000_certificate.png") is None


@pytest.mark.parametrize("name", [
    "Asha_20261005_120000_certificate.png",            # the original format still resolves
    "Asha_20261005_120000_certificate.txt",
    "Asha_20261005_120000_1a2b3c4d_certificate.png",   # the new format with a uuid suffix
])
def test_generated_formats_are_accepted(service, name):
    (service.output_dir / name).write_bytes(b"x")
    assert service._resolve_safe(name) == (service.output_dir / name).resolve()


@pytest.mark.parametrize("name", [
    "../secret_20261005_120000_certificate.png",
    "a/b_20261005_120000_certificate.png",
    "Asha_20261005_120000_ZZZZZZZZ_certificate.png",   # suffix must be lowercase hex
    "Asha_20261005_120000_1a2b3c_certificate.png",     # ...and exactly eight characters
    "Asha_20261005_120000_certificate.exe",
])
def test_other_names_are_rejected(service, name):
    assert service._resolve_safe(name) is None


# ------------------------------------------------------------------ same-second collisions

@pytest.mark.asyncio
async def test_two_certificates_in_the_same_second_do_not_overwrite_each_other(service, monkeypatch):
    monkeypatch.setattr(cs, "datetime", _Clock)

    first = await service.generate_certificate("Asha Rao", "2026-10-05", "O+", "Chennai")
    second = await service.generate_certificate("Asha Rao", "2026-10-05", "O+", "Chennai")

    assert first != second
    assert Path(first).is_file() and Path(second).is_file()
    for path in (first, second):
        assert await service.get_certificate(Path(path).name) is not None, "the new name must pass _resolve_safe"


@pytest.mark.asyncio
async def test_placeholder_certificates_are_unique_too(service, monkeypatch):
    monkeypatch.setattr(cs, "datetime", _Clock)
    monkeypatch.setattr(cs, "PILLOW_AVAILABLE", False)
    a = await service.generate_certificate("Asha Rao", "2026-10-05", "O+", "Chennai")
    b = await service.generate_certificate("Asha Rao", "2026-10-05", "O+", "Chennai")
    assert a != b and Path(a).is_file() and Path(b).is_file()


# ------------------------------------------------------------------ encoding

@pytest.mark.asyncio
async def test_placeholder_is_written_as_utf8_whatever_the_platform_default(service, monkeypatch):
    monkeypatch.setattr(cs, "PILLOW_AVAILABLE", False)
    name = "ä¸­æ–‡ à¤¨à¤¾à¤® ZoÃ«"  # not representable in cp1252

    path = await service.generate_certificate(name, "2026-10-05", "O+", "Chennai")

    assert name in Path(path).read_text(encoding="utf-8")


# ------------------------------------------------------------------ attachment header

def _disposition(filename: str) -> str:
    message = MIMEMultipart()
    asyncio.run(EmailService(get_settings())._attach_file(message, _file(filename)))
    return message.get_payload()[0]["Content-Disposition"]


def _file(filename: str) -> Path:
    path = Path(__file__).parent / "_attach_tmp" / filename
    path.parent.mkdir(exist_ok=True)
    from PIL import Image
    with Image.new("RGB", (1, 1)) as image:
        image.save(path, format="PNG")
    return path


@pytest.fixture(autouse=True)
def _cleanup_attachments():
    yield
    import shutil
    shutil.rmtree(Path(__file__).parent / "_attach_tmp", ignore_errors=True)


def test_attachment_filename_is_quoted():
    assert _disposition("Asha_20261005_120000_certificate.png") == (
        'attachment; filename="Asha_20261005_120000_certificate.png"'
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Windows forbids some of these characters in file names")
def test_attachment_filename_cannot_break_out_of_the_header():
    header = _disposition('a b";x=y.png')
    assert header.startswith("attachment; filename=")
    assert 'filename="a b";x=y.png"' not in header  # the quote and semicolon are escaped or encoded


def test_attachment_filename_with_a_space_stays_one_parameter():
    header = _disposition("two words.png")
    assert header == 'attachment; filename="two words.png"'
async def test_email_with_unusable_attachment_is_not_sent(tmp_path, monkeypatch):
    from unittest.mock import AsyncMock
    from app.services import email_service

    deliver = AsyncMock()
    monkeypatch.setattr(email_service.aiosmtplib, "send", deliver)
    service = EmailService(get_settings())
    missing = tmp_path / "missing.png"
    invalid = tmp_path / "invalid.png"
    invalid.write_text("invalid image", encoding="utf8")
    for path in (missing, invalid):
        assert not await service.send_certificate_email("recipient@example.com", "Recipient", path)
    deliver.assert_not_awaited()


async def test_file_alias_is_never_resolved_for_deletion(service):
    name = "older_20261101_012345_certificate.txt"
    original = service.output_dir / name
    original.write_text("original", encoding="utf8")
    alias = service.output_dir / "alias_20261101_012345_certificate.txt"
    try:
        alias.symlink_to(original)
    except OSError as err:
        if getattr(err, "winerror", None) == 1314:
            pytest.skip("Windows account lacks symlink privilege")
        raise
    assert await service.get_certificate(alias.name) is None
    assert await service.list_certificates() == [name]
    assert not await service.delete_certificate(alias.name)
    assert original.read_text(encoding="utf8") == "original"

def test_retention_removes_only_managed_regular_files(service):
    import os
    expired = service.output_dir / "old_20260101_000001_certificate.txt"
    unfinished = service.output_dir / ".lc-cert-example.tmp"
    unrelated = service.output_dir / "volume-marker"
    fresh = service.output_dir / "new_20260101_000002_certificate.txt"
    for path in (expired, unfinished, unrelated, fresh):
        path.write_text("synthetic", encoding="utf8")
    for path in (expired, unfinished, unrelated):
        os.utime(path, (1, 1))
    assert service.purge_expired_files(2) == 2
    assert {file.name for file in service.output_dir.iterdir()} == {fresh.name, unrelated.name}

def test_retention_can_finish_interrupted_publication(service):
    import os
    published = service.output_dir / "old_20260101_000001_certificate.txt"
    temporary = service.output_dir / ".lc-cert-interrupted.tmp"
    temporary.write_text("synthetic", encoding="utf8")
    os.link(temporary, published)
    os.utime(temporary, (1, 1))
    service.purge_expired_files(2)
    service.purge_expired_files(2)
    assert not published.exists() and not temporary.exists()
