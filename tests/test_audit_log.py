"""P3-58: state-changing admin actions leave an audit row; failures and reads do not."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.audit import AdminAuditLog
from tests.helpers import insert_donor, insert_request

ADMIN = "ADM-test123"  # the admin minted by the admin_client fixture
HOSPITAL = {
    "hospital_name": "Audit Care", "hospital_address": "5 Audit Road", "pincode": "600009",
    "city": "Chennai", "state": "Tamil Nadu", "country": "India",
}


async def _rows(session) -> list[AdminAuditLog]:
    return list((await session.execute(select(AdminAuditLog).order_by(AdminAuditLog.id))).scalars())


@pytest.mark.asyncio
async def test_blood_request_decisions_are_audited(admin_client: AsyncClient, test_session):
    await insert_request(test_session, 1, status="Pending")
    await insert_request(test_session, 2, status="Pending")
    assert (await admin_client.post("/api/v1/blood-requests/REQ-1/approve", params={"send_emails": "false"})).status_code == 200
    assert (await admin_client.post("/api/v1/blood-requests/REQ-2/decline")).status_code == 200
    rows = await _rows(test_session)
    assert [(r.admin_id, r.action, r.entity_id) for r in rows] == [
        (ADMIN, "blood_request.approve", "REQ-1"),
        (ADMIN, "blood_request.decline", "REQ-2"),
    ]
    assert all(r.created_at for r in rows)


@pytest.mark.asyncio
async def test_hospital_crud_is_audited(admin_client: AsyncClient, test_session):
    created = (await admin_client.post("/api/v1/hospitals/", json=HOSPITAL)).json()
    hid = created["id"]
    assert (await admin_client.patch(f"/api/v1/hospitals/{hid}", json={"landmark": "Near park"})).status_code == 200
    assert (await admin_client.delete(f"/api/v1/hospitals/{hid}")).status_code == 200
    rows = await _rows(test_session)
    assert [r.action for r in rows] == ["hospital.create", "hospital.update", "hospital.delete"]
    assert rows[1].detail == "fields=landmark"
    assert {r.entity_id for r in rows} == {hid}


@pytest.mark.asyncio
async def test_donor_status_changes_are_audited(admin_client: AsyncClient, test_session):
    await insert_donor(test_session)
    assert (await admin_client.post("/api/v1/donors/DON-1/deactivate")).status_code == 200
    assert (await admin_client.post("/api/v1/donors/DON-1/activate")).status_code == 200
    assert [r.action for r in await _rows(test_session)] == ["donor.deactivate", "donor.activate"]


@pytest.mark.asyncio
async def test_failed_actions_and_reads_write_nothing(admin_client: AsyncClient, test_session):
    assert (await admin_client.post("/api/v1/blood-requests/NOPE/approve")).status_code == 404
    assert (await admin_client.delete("/api/v1/hospitals/NOPE")).status_code == 404
    assert (await admin_client.get("/api/v1/blood-requests/pending")).status_code == 200
    assert (await admin_client.get("/api/v1/hospitals/")).status_code == 200
    assert await _rows(test_session) == []


@pytest.mark.asyncio
async def test_invite_audit_row_holds_no_email(admin_client: AsyncClient, test_session, monkeypatch):
    from app.services import email_service

    async def fake_send(self, *a, **k):
        return True

    monkeypatch.setattr(email_service.EmailService, "send_otp_email", fake_send)
    r = await admin_client.post("/api/v1/admins/invite", json={"email": "new.admin@example.com"})
    assert r.status_code == 200
    (row,) = await _rows(test_session)
    assert row.action == "admin.invite" and row.admin_id == ADMIN
    assert "example.com" not in " ".join(filter(None, [row.entity_id, row.detail]))
