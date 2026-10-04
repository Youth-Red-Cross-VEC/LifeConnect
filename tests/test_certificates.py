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
            # attacker-controlled identity must be ignored
            "donor_email": "attacker@evil.example",
            "donor_name": "Someone Else",
        },
    )
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
