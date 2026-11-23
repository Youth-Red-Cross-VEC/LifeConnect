"""Certificate generation must derive donor identity server-side (P0-06)."""

import pytest
from httpx import AsyncClient

from app.main import app
from app.services.certificate_service import CertificateService, get_certificate_service
from app.services.email_service import get_email_service
from tests.helpers import insert_donor, insert_request


class FakeEmail:
    def __init__(self):
        self.sent = []

    async def send_certificate(self, donor_name, donor_email, certificate_path):
        self.sent.append((donor_name, donor_email))
        return True


@pytest.fixture
def fake_email():
    fake = FakeEmail()
    app.dependency_overrides[get_email_service] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_email_service, None)


@pytest.fixture
def cert_service(tmp_path):
    service = CertificateService(
        template_dir=str(tmp_path / "templates"), output_dir=str(tmp_path / "out")
    )
    app.dependency_overrides[get_certificate_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_certificate_service, None)


@pytest.mark.asyncio
async def test_generate_uses_donor_record_not_client_identity(
    admin_client: AsyncClient, test_session, fake_email, cert_service
):
    await insert_donor(test_session, 1, blood_group="A+")

    response = await admin_client.post(
        "/api/v1/certificates/generate",
        json={
            "donor_id": "DON-1",
            "donation_date": "2026-01-15",
            "location": "Example Hospital",
            # Extra identity fields must be rejected before delivery.
            "donor_email": "attacker@evil.example",
            "donor_name": "Someone Else",
        },
    )
    assert response.status_code == 422
    assert fake_email.sent == []
    response = await admin_client.post("/api/v1/certificates/generate", json={
        "donor_id": "DON-1", "donation_date": "2026-01-15", "location": "Example Hospital",
    })
    assert response.status_code == 201, response.text
    assert fake_email.sent == [("Donor1 Test", "donor1@example.com")]


@pytest.mark.asyncio
async def test_generate_unknown_donor_returns_404(admin_client: AsyncClient, fake_email, cert_service):
    response = await admin_client.post(
        "/api/v1/certificates/generate",
        json={"donor_id": "DON-missing", "donation_date": "2026-01-15"},
    )
    assert response.status_code == 404
    assert fake_email.sent == []


@pytest.mark.asyncio
async def test_generate_takes_location_from_request_when_given(
    admin_client: AsyncClient, test_session, fake_email, cert_service
):
    await insert_donor(test_session, 1)
    await insert_request(test_session, 1)

    response = await admin_client.post(
        "/api/v1/certificates/generate",
        json={"donor_id": "DON-1", "request_id": "REQ-1", "donation_date": "2026-01-15"},
    )
    assert response.status_code == 201, response.text
    assert fake_email.sent == [("Donor1 Test", "donor1@example.com")]


@pytest.mark.asyncio
async def test_generate_unknown_request_returns_404(
    admin_client: AsyncClient, test_session, fake_email, cert_service
):
    await insert_donor(test_session, 1)
    response = await admin_client.post(
        "/api/v1/certificates/generate",
        json={"donor_id": "DON-1", "request_id": "REQ-nope", "donation_date": "2026-01-15"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_requires_a_donation_date(
    admin_client: AsyncClient, test_session, fake_email, cert_service
):
    await insert_donor(test_session, 1)
    response = await admin_client.post("/api/v1/certificates/generate", json={"donor_id": "DON-1"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_requires_admin(client: AsyncClient):
    response = await client.post("/api/v1/certificates/generate", json={"donor_id": "DON-1"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_uses_recorded_donation_date_from_request(
    admin_client: AsyncClient, test_session, fake_email, cert_service
):
    from datetime import date

    from app.models.blood_request import ResponseDetails

    await insert_donor(test_session, 1)
    await insert_request(test_session, 1)
    (await test_session.get(ResponseDetails, "RESP-1")).donation_date = date(2026, 2, 3)
    await test_session.commit()

    response = await admin_client.post(
        "/api/v1/certificates/generate", json={"donor_id": "DON-1", "request_id": "REQ-1"}
    )
    assert response.status_code == 201, response.text

async def test_certificate_delivery_is_bound_to_generation_record(admin_client, test_session, fake_email, cert_service):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    generated = await admin_client.post("/api/v1/certificates/generate", json={
        "donor_id": "DON-1", "donation_date": "2026-01-15", "send_email": False,
    })
    assert generated.status_code == 201
    params = {"filename": generated.json()["filename"], "donor_id": "DON-2"}
    url = "/api/v1/certificates/send-email"
    assert (await admin_client.post(url, params=params)).status_code == 404
    assert fake_email.sent == []
    params["donor_id"] = "DON-1"
    assert (await admin_client.post(url, params=params)).status_code == 200
    assert fake_email.sent == [("Donor1 Test", "donor1@example.com")]


async def test_certificate_page_excludes_pending_erasure_before_pagination(admin_client, test_session, cert_service):
    from app.models.privacy import ErasureFile

    cert_service.output_dir.mkdir()
    names = [f"Donor{n}_20261123_100000_certificate.png" for n in range(4)]
    for name in names:
        (cert_service.output_dir / name).touch()
    test_session.add(ErasureFile(filename=names[0]))
    await test_session.commit()
    response = await admin_client.get("/api/v1/certificates/", params={"offset": 1, "limit": 1})
    assert response.status_code == 200
    assert response.json() == {"certificates": [names[2]], "total": 3}


async def test_certificate_download_uses_verified_bytes_and_headers(admin_client, test_session, cert_service, monkeypatch):
    from app.services import certificate_service as module
    await insert_donor(test_session)
    for image in (True, False):
        monkeypatch.setattr(module, "PILLOW_AVAILABLE", image)
        generated = await admin_client.post("/api/v1/certificates/generate", json={
            "donor_id": "DON-1", "donation_date": "2026-01-15", "send_email": False,
        })
        assert generated.status_code == 201
        name = generated.json()["filename"]
        assert "donor" not in name.lower()
        response = await admin_client.get(f"/api/v1/certificates/download/{name}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/png" if image else "text/plain")
        assert response.headers["content-disposition"] == f'attachment; filename="{name}"'
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "no-store" in response.headers["cache-control"]
        assert response.content == (cert_service.output_dir / name).read_bytes()
        if image:
            (cert_service.output_dir / name).write_bytes(b"unexpected file content")
            assert (await admin_client.get(f"/api/v1/certificates/download/{name}")).status_code == 404


async def test_unsafe_entries_cannot_be_delivered_or_delete_another_file(admin_client, cert_service, tmp_path):
    import os
    from app.services.certificate_service import MAX_CERTIFICATE_BYTES, read_certificate_bytes
    cert_service.output_dir.mkdir()
    name = "legacy_20260101_100000_certificate.txt"
    entry = cert_service.output_dir / name
    original = tmp_path / "separate-file"
    original.write_text("synthetic", encoding="utf8")
    os.link(original, entry)
    assert (await admin_client.get(f"/api/v1/certificates/download/{name}")).status_code == 404
    assert (await admin_client.get("/api/v1/certificates/")).json()["total"] == 0
    assert (await admin_client.delete(f"/api/v1/certificates/{name}")).status_code == 404
    with pytest.raises(ValueError):
        read_certificate_bytes(entry)
    assert original.read_text() == "synthetic"
    entry.unlink()
    with entry.open("wb") as out:
        out.truncate(MAX_CERTIFICATE_BYTES + 1)
    assert (await admin_client.get(f"/api/v1/certificates/download/{name}")).status_code == 404


async def test_generation_collision_preserves_original(cert_service, monkeypatch):
    from pathlib import Path
    from app.services import certificate_service as module
    monkeypatch.setattr(module, "_new_filename", lambda ext: "fixed_20260101_100000_certificate." + ext)
    first = Path(await cert_service.generate_certificate("Donor One", "Today", "A+", "Hospital"))
    contents = first.read_bytes()
    with pytest.raises(FileExistsError):
        await cert_service.generate_certificate("Donor Two", "Today", "B+", "Hospital")
    assert first.read_bytes() == contents
    assert list(cert_service.output_dir.iterdir()) == [first]
