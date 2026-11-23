"""Part C4: clients cannot set ids, roles, status, counters or ownership through request bodies."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.admin import AdminDetails
from app.models.blood_request import BloodRequestDetails
from app.models.donor import DonorDetail
from app.models.hospital import HospitalDetails
from app.models.query import QueryTable
from tests.helpers import insert_admin, insert_donor, insert_request, registration_payload

PRIVILEGED = {
    "id": "DON-HIJACK", "authentication_id": "AUTH-HIJACK", "active_status": False, "role": "admin",
    "user_type": "admin", "is_admin": True, "number_of_times_donated": 99, "last_donated_date": "2020-01-01T00:00:00",
    "password": "Hijacked123", "email": "hijack@example.com", "approved_donation_count": 99,
    "closed_requests_count": 99, "status": "Closed", "approved_admin_id": "ADM-HIJACK", "donor_id": "DON-OTHER",
    "admin_id": "ADM-HIJACK", "admin_name": "Hijacker", "admin_response": "I answered myself",
}


@pytest.mark.asyncio
async def test_registration_rejects_privileged_fields(client: AsyncClient, test_session, verified_registration):
    body = {**registration_payload("fresh@example.com"), **PRIVILEGED, "email": "fresh@example.com", "password": "Secret123"}
    r = await verified_registration(client, body)
    assert r.status_code == 422
    assert (await test_session.scalars(select(DonorDetail))).first() is None
    r = await verified_registration(client, registration_payload("fresh@example.com"))
    assert r.status_code == 201

    donor = (await test_session.execute(select(DonorDetail))).scalar_one()
    assert donor.id != "DON-HIJACK" and donor.authentication_id != "AUTH-HIJACK"
    assert donor.active_status is True and donor.number_of_times_donated == 0
    assert donor.last_donated_date is None and donor.email == "fresh@example.com"


@pytest.mark.asyncio
async def test_donor_update_changes_only_the_profile_fields(client: AsyncClient, test_session):
    from app.api.auth.utils import create_access_token

    await insert_donor(test_session, 1)
    token = create_access_token({"sub": "DON-1", "user_type": "donor", "email": "donor1@example.com"})
    r = await client.patch("/api/v1/donors/DON-1", json={**PRIVILEGED, "name": "Renamed Donor", "active_status": True},
                           headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422
    r = await client.patch("/api/v1/donors/DON-1", json={"name": "Renamed Donor"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text

    test_session.expire_all()
    donor = await test_session.get(DonorDetail, "DON-1")
    assert donor.name == "Renamed Donor"
    assert donor.email == "donor1@example.com" and donor.authentication_id == "AUTH-1"
    assert donor.number_of_times_donated == 0 and donor.last_donated_date is None
    assert donor.password != "Hijacked123"


@pytest.mark.asyncio
async def test_admin_update_cannot_touch_credentials_counters_or_ids(admin_client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    r = await admin_client.put("/api/v1/admins/ADM-1", json={**PRIVILEGED, "active_status": "Active", "department": "Ops"})
    assert r.status_code == 422
    r = await admin_client.put("/api/v1/admins/ADM-1", json={"department": "Ops"})
    assert r.status_code == 200, r.text

    test_session.expire_all()
    admin = await test_session.get(AdminDetails, "ADM-1")
    assert admin.department == "Ops"
    assert admin.email == "admin1@example.com" and admin.authentication_id == "AUTHADM-1"
    assert admin.approved_donation_count == 0 and admin.closed_requests_count == 0
    assert admin.password != "Hijacked123"


@pytest.mark.asyncio
async def test_hospital_update_cannot_change_the_id_or_country(admin_client: AsyncClient, test_session):
    await insert_request(test_session, 1)  # creates HOSP-1
    r = await admin_client.patch("/api/v1/hospitals/HOSP-1", json={"id": "HOSP-HIJACK", "country": "Mars", "city": "Madurai"})
    assert r.status_code == 422
    r = await admin_client.patch("/api/v1/hospitals/HOSP-1", json={"city": "Madurai"})
    assert r.status_code == 200, r.text

    test_session.expire_all()
    hospital = await test_session.get(HospitalDetails, "HOSP-1")
    assert hospital is not None and hospital.city == "Madurai" and hospital.country == "India"


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["hospital_name", "hospital_address", "pincode", "city", "state"])
async def test_hospital_update_rejects_null_for_required_fields(admin_client: AsyncClient, test_session, field):
    await insert_request(test_session, 1)
    r = await admin_client.patch("/api/v1/hospitals/HOSP-1", json={field: None})
    assert r.status_code == 422, "an explicit null for a required column must be a clear 422, not a database error"


@pytest.mark.asyncio
async def test_hospital_update_can_still_clear_optional_fields(admin_client: AsyncClient, test_session):
    await insert_request(test_session, 1)
    assert (await admin_client.patch("/api/v1/hospitals/HOSP-1", json={"landmark": "Near the park"})).status_code == 200
    r = await admin_client.patch("/api/v1/hospitals/HOSP-1", json={"landmark": None, "branch": None})
    assert r.status_code == 200 and r.json()["landmark"] is None


@pytest.mark.asyncio
async def test_public_blood_request_cannot_choose_its_own_status_or_approver(client: AsyncClient, test_session):
    from datetime import datetime, timedelta

    await insert_request(test_session, 1)
    body = {
        "patient_name": "Sample Patient", "blood_group": "O+", "hospital_id": "HOSP-1", "contact_number": "9000200001",
        "patient_age": 40, "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat(), "units_required": 1,
    }
    assert (await client.post("/api/v1/blood-requests/", json={**body, **PRIVILEGED})).status_code == 422
    r = await client.post("/api/v1/blood-requests/", json=body)
    assert r.status_code == 201, r.text
    created = (await test_session.execute(
        select(BloodRequestDetails).where(BloodRequestDetails.id == r.json()["id"])
    )).scalar_one()
    assert created.status == "Pending"
    assert created.approved_admin_id is None and created.closed_admin_id is None


@pytest.mark.asyncio
async def test_a_query_body_cannot_claim_ownership_or_an_admin_answer(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    body = {
        "user_name": "Visitor", "user_email": "visitor@example.com", "user_query": "A question about donating",
    }
    assert (await client.post("/api/v1/queries/", json={**body, **PRIVILEGED})).status_code == 422
    r = await client.post("/api/v1/queries/", json=body)
    assert r.status_code == 201, r.text
    row = (await test_session.execute(select(QueryTable))).scalar_one()
    assert row.donor_id is None, "ownership comes only from the authenticated donor"
    assert row.admin_id == "PENDING" and row.admin_name == "PENDING" and row.admin_response is None
