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
    assert service._resolve_safe("Asha_٢٠٢٦١٠٠٥_120000_certificate.png") is None


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
    name = "中文 नाम Zoë"  # not representable in cp1252

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
    path.write_bytes(b"x")
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
