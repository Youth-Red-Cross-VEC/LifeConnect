"""Verify certificate publication, template consistency and bounded cleanup on isolated storage."""
import os
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from app.services import certificate_service as cs


async def test_shipped_template_is_used_and_source_is_preserved(tmp_path):
    service = cs.CertificateService(output_dir=str(tmp_path))
    source = service.template_dir / "template1.png"
    original = source.read_bytes()
    assert original == Path("frontend/public/images/certificate_templates/template1.png").read_bytes()
    result = Path(await service.generate_certificate("Synthetic", "2026-11-24", "O+", "Test Hospital"))
    assert "Synthetic" not in result.name
    with Image.open(result) as generated, Image.open(source) as template:
        assert generated.size == template.size
        delta = ImageChops.difference(generated.convert("RGB"), template.convert("RGB"))
        for box in [(328, 187, 600, 230), (215, 417, 460, 450),
                    (675, 188, 770, 235), (267, 455, 700, 490)]:
            assert delta.crop(box).getbbox()
    assert source.read_bytes() == original


async def test_damaged_template_recovers_and_placeholder_keeps_details(tmp_path, monkeypatch):
    service = cs.CertificateService(str(tmp_path), str(tmp_path / "private"))
    (tmp_path / "template1.png").write_bytes(b"damaged")
    result = Path(await service.generate_certificate("Synthetic", "2026-11-24", "O+", "Test Hospital"))
    with Image.open(result) as generated:
        assert generated.size == (800, 600)
    monkeypatch.setattr(cs, "PILLOW_AVAILABLE", False)
    result = Path(await service.generate_certificate("Synthetic", "2026-11-24", "O+", "Test Hospital"))
    content = cs.read_certificate_bytes(result).decode()
    assert all(value in content for value in ("Synthetic", "2026-11-24", "O+", "Test Hospital"))


def test_publication_failure_and_name_collision_preserve_existing_data(tmp_path, monkeypatch):
    service = cs.CertificateService(output_dir=str(tmp_path))
    def broken(stream):
        stream.write(b"partial")
        raise OSError("synthetic write failure")
    with pytest.raises(OSError):
        service._publish_certificate("txt", broken)
    assert list(tmp_path.iterdir()) == []

    name = "Synthetic_20261124_120000_certificate.txt"
    monkeypatch.setattr(cs, "_new_filename", lambda extension: name)
    path = Path(service._publish_certificate("txt", lambda stream: stream.write(b"first")))
    with pytest.raises(FileExistsError):
        service._publish_certificate("txt", lambda stream: stream.write(b"second"))
    assert list(tmp_path.iterdir()) == [path]
    assert path.read_bytes() == b"first"


def test_retention_only_unlinks_expired_managed_files(tmp_path):
    service = cs.CertificateService(output_dir=str(tmp_path))
    for name in ("Legacy_20261124_120000_certificate.txt", ".lc-cert-dead.tmp", "operator.txt",
                 "Current_20261124_120000_certificate.txt"):
        path = tmp_path / name
        path.write_bytes(b"synthetic")
        os.utime(path, (100, 200 if name.startswith("Current") else 100))
    assert service.purge_expired_files(200) == 2
    assert service.purge_expired_files(200) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Current_20261124_120000_certificate.txt", "operator.txt"]
