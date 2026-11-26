from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.request_status import AdminRole
from app.main import app
from app.models.audit import AdminAuditLog
from app.models.blood_request import BloodRequestDetails, ResponseDetails
from app.models.donor import (
    AddressDetails,
    AuthenticationDetailsDonor,
    DiseaseDetails,
    DonorDetail,
    PersonalDetails,
)
from app.models.otp import OtpCode
from app.models.privacy import ErasureFile, ErasureRequest
from app.models.query import QueryTable
from app.models.refresh_session import RefreshSession
from app.services.certificate_service import CertificateService, get_certificate_service
from app.services.otp_service import PURPOSE_ADMIN_RESET, PURPOSE_DONOR_RESET, store_otp
from tests.helpers import cookie_headers, insert_admin, insert_donor, insert_request, refresh_cookie

URL = "/api/v1/privacy/erasure-requests"


async def login(client, role, email):
    response = await client.post(f"/api/v1/auth/{role}/login", json={"email": email, "password": "Secret123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, refresh_cookie(response)


async def test_erasure_rejects_unauthorized_and_invalid_submissions(client, test_session):
    await insert_donor(test_session)
    await insert_admin(test_session, 1, role=AdminRole.ADMIN)
    donor, _ = await login(client, "donor", "donor1@example.com")
    admin, _ = await login(client, "admin", "admin1@example.com")
    correct = {"current_password": "Secret123"}
    assert (await client.post(URL, json=correct)).status_code == 401
    assert (await client.post(URL, headers=admin, json=correct)).status_code == 403
    assert (await client.post(URL, headers=donor, json={"current_password": "Wrong123"})).status_code == 403
    invalid = await client.post(URL, headers=donor, json={"current_password": {"sensitive": "hide-me"}})
    assert invalid.status_code == 422 and "hide-me" not in invalid.text


async def test_erasure_requires_password_ownership_and_super_admin(client, test_session):
    await insert_donor(test_session)
    await insert_donor(test_session, 2)
    await insert_admin(test_session, 1, role=AdminRole.ADMIN)
    await insert_admin(test_session, 2, role=AdminRole.SUPER_ADMIN)
    donor, _ = await login(client, "donor", "donor1@example.com")
    other, _ = await login(client, "donor", "donor2@example.com")
    admin, _ = await login(client, "admin", "admin1@example.com")
    reviewer, _ = await login(client, "admin", "admin2@example.com")
    correct = {"current_password": "Secret123"}
    submitted = await client.post(URL, headers=donor, json={**correct, "donor_id": "DON-2"})
    assert submitted.status_code == 202
    receipt = submitted.json()
    assert (await client.post(URL, headers=donor, json=correct)).json()["id"] == receipt["id"]
    assert (await client.get(f"{URL}/mine", headers=other)).json() is None
    assert (await client.get(URL, headers=donor)).status_code == 403
    queue = (await client.get(URL, headers=reviewer)).json()
    assert [item["donor_id"] for item in queue] == ["DON-1"]
    review = f"{URL}/{receipt['id']}"
    assert (await client.patch(review, headers=admin, json={"decision": "approve"})).status_code == 403
    assert (await client.patch(review, headers=other, json={"decision": "approve"})).status_code == 403
    rejected = await client.patch(review, headers=reviewer, json={"decision": "reject"})
    assert rejected.json()["status"] == "rejected"
    assert (await client.get(f"{URL}/mine", headers=donor)).json()["status"] == "rejected"
    assert (await client.patch(review, headers=reviewer, json={"decision": "approve"})).status_code == 409


async def test_erasure_removes_linked_data_and_sessions_but_retains_request_statistics(
    client, test_session, tmp_path,
):
    donor = await insert_donor(test_session)
    other = await insert_donor(test_session, 2)
    await insert_admin(test_session, 1, role=AdminRole.SUPER_ADMIN)
    await insert_request(test_session, 1, status="Closed", units_required=2)
    response = await test_session.get(ResponseDetails, "RESP-1")
    response.donor_ids = "DON-12, DON-1,DON-2"
    response.units_donated = 2
    response.report = "Synthetic donor details"
    test_session.add_all([
        AuthenticationDetailsDonor(auth_id=donor.authentication_id, name=donor.name),
        QueryTable(donor_id=donor.id, user_name="Synthetic", user_email="donor1@example.com",
                   admin_id="ADM-1", admin_name="Reviewer", user_query="Synthetic content"),
        QueryTable(donor_id=other.id, user_name="Other", user_email="donor2@example.com",
                   admin_id="ADM-1", admin_name="Reviewer", user_query="Keep this"),
        AdminAuditLog(admin_id="ADM-1", action="donor.activate", entity_type="donor", entity_id=donor.id),
    ])
    filename = "Synthetic_20261121_120000_certificate.txt"
    (tmp_path / filename).write_text("Synthetic certificate", encoding="utf-8")
    test_session.add(AdminAuditLog(admin_id="ADM-1", action="certificate.generate", entity_type="certificate",
                                  entity_id=filename, detail=f"donor_id={donor.id}"))
    await test_session.commit()
    await store_otp(test_session, donor.email, "123456", PURPOSE_DONOR_RESET)
    await store_otp(test_session, donor.email, "654321", PURPOSE_ADMIN_RESET)
    credentials, old_cookie = await login(client, "donor", donor.email)
    reviewer, _ = await login(client, "admin", "admin1@example.com")
    submitted = await client.post(URL, headers=credentials, json={"current_password": "Secret123"})
    assert submitted.status_code == 202
    review = f"{URL}/{submitted.json()['id']}"
    result = await client.patch(review, headers=reviewer, json={"decision": "approve"})
    assert result.status_code == 200 and result.json()["status"] == "completed"
    assert (await client.get(f"{URL}/mine", headers=credentials)).status_code == 401
    assert (await client.post("/api/v1/auth/refresh", headers=cookie_headers(old_cookie))).status_code == 401
    assert await test_session.get(DonorDetail, "DON-1") is None
    assert await test_session.get(DonorDetail, "DON-2") is not None
    for model, key in ((PersonalDetails, "PD-1"), (AddressDetails, "AD-1"), (DiseaseDetails, "DS-1")):
        assert await test_session.get(model, key) is None
    assert await test_session.scalar(select(func.count()).select_from(AuthenticationDetailsDonor).where(
        AuthenticationDetailsDonor.auth_id == "AUTH-1",
    )) == 0
    assert await test_session.scalar(select(func.count()).select_from(RefreshSession).where(
        RefreshSession.user_id == "DON-1",
    )) == 0
    assert list(await test_session.scalars(select(QueryTable.donor_id))) == ["DON-2"]
    assert list(await test_session.scalars(select(OtpCode.purpose))) == [PURPOSE_ADMIN_RESET]
    await test_session.refresh(response)
    assert (response.donor_ids, response.units_donated, response.report) == ("DON-12,DON-2", 2, None)
    assert (await test_session.get(BloodRequestDetails, "REQ-1")).status == "Closed"
    receipt = await test_session.get(ErasureRequest, submitted.json()["id"])
    assert receipt.donor_id is None
    assert await test_session.get(ErasureFile, filename) is not None
    assert await test_session.scalar(select(func.count()).select_from(AdminAuditLog).where(
        AdminAuditLog.entity_id.in_([filename, "DON-1"]),
    )) == 0
    certs = CertificateService(output_dir=str(tmp_path))
    app.dependency_overrides[get_certificate_service] = lambda: certs
    assert (await client.get("/api/v1/certificates/", headers=reviewer)).json()["certificates"] == []
    assert (await client.get(f"/api/v1/certificates/download/{filename}", headers=reviewer)).status_code == 404


async def test_erasure_failure_rolls_back_all_database_changes(client, test_session, monkeypatch):
    await insert_donor(test_session)
    await insert_admin(test_session, 1, role=AdminRole.SUPER_ADMIN)
    donor, _ = await login(client, "donor", "donor1@example.com")
    reviewer, _ = await login(client, "admin", "admin1@example.com")
    submitted = await client.post(URL, headers=donor, json={"current_password": "Secret123"})
    review = f"{URL}/{submitted.json()['id']}"
    privacy = import_module("app.api.v1.privacy")
    original = privacy.erase_donor

    async def fail(session, account):
        await original(session, account)
        raise HTTPException(500, "Synthetic rollback")

    with monkeypatch.context() as patch:
        patch.setattr(privacy, "erase_donor", fail)
        assert (await client.patch(review, headers=reviewer, json={"decision": "approve"})).status_code == 500
    assert (await client.get(f"{URL}/mine", headers=donor)).json()["status"] == "pending"
    assert (await client.patch(review, headers=reviewer, json={"decision": "approve"})).status_code == 200


async def test_certificate_erasure_queue_retries_and_removes_file(test_session, tmp_path, monkeypatch):
    jobs = import_module("app.tasks.scheduled_jobs")
    certs = CertificateService(output_dir=str(tmp_path))
    filename = "Synthetic_20261121_120000_certificate.txt"
    path = tmp_path / filename
    path.write_text("Synthetic certificate", encoding="utf-8")
    test_session.add(ErasureFile(filename=filename))
    await test_session.commit()
    monkeypatch.setattr(jobs, "get_certificate_service", lambda: certs)

    class Database:
        @asynccontextmanager
        async def session(self):
            yield test_session
            await test_session.commit()

    async def fail(filename):
        raise PermissionError

    with monkeypatch.context() as patch:
        patch.setattr(certs, "delete_certificate", fail)
        await jobs.purge_old_certificates(Database())
    assert path.exists()
    assert await test_session.get(ErasureFile, filename) is not None
    await jobs.purge_old_certificates(Database())
    assert not path.exists()
    assert await test_session.get(ErasureFile, filename) is None
