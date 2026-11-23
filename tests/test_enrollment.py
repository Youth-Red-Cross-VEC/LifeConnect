"""Mailbox ownership is required before registration can disclose account availability."""
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.email_service import EmailService
from tests.helpers import insert_admin, insert_donor, registration_payload

REGISTER = "/api/v1/donors/register"


async def test_registration_code_protects_membership_and_enables_login(client, test_session, monkeypatch):
    await insert_donor(test_session)
    await insert_admin(test_session, 1)
    sent = {}

    async def capture(self, email, otp, name, purpose):
        assert purpose == "donor_enrollment"
        sent[email] = otp
        return True

    monkeypatch.setattr(EmailService, "send_otp_email", capture)
    replies = []
    addresses = ("donor1@example.com", "admin1@example.com", "new@example.com")
    for index, email in enumerate(addresses, 1):
        transport = ASGITransport(app=app, client=(f"192.0.2.{index}", 4000))
        async with AsyncClient(transport=transport, base_url="http://test") as visitor:
            body = registration_payload(email)
            request = await visitor.post(f"{REGISTER}/code", json={"email": email})
            assert request.status_code == 200
            replies.append(request.json())
            missing = await visitor.post(REGISTER, json=body)
            assert missing.status_code == 422
            assert body["password"] not in missing.text
            invalid = await visitor.post(REGISTER, json={**body, "enrollment_code": f"{(int(sent[email]) + 1) % 1000000:06d}"})
            assert invalid.status_code == 400
            assert invalid.json()["detail"] == "Invalid or expired registration code"
    assert replies[0] == replies[1] == replies[2]
    email = "new@example.com"
    body = {**registration_payload(email), "enrollment_code": sent[email]}
    assert (await client.post(REGISTER, json=body)).status_code == 201
    assert (await client.post(REGISTER, json=body)).status_code == 400
    login = await client.post("/api/v1/auth/donor/login", json={"email": email, "password": body["password"]})
    assert login.status_code == 200
