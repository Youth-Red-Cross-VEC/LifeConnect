"""Blood request status transitions are defined once and enforced by the API."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.request_status import TRANSITIONS, BloodRequestStatus as S, can_transition, sources_for
from app.models.blood_request import BloodRequestDetails
from app.repositories.blood_request import BloodRequestRepository
from tests.helpers import insert_request

P = "/api/v1/blood-requests"


def test_every_status_has_a_row_in_the_table():
    assert set(TRANSITIONS) == set(S)


@pytest.mark.parametrize("src,dst,ok", [
    ("Pending", S.APPROVED, True),
    ("Pending", S.DECLINED, True),
    ("Pending", S.CLOSED, False),
    ("Approved", S.CLOSED, True),
    ("Approved", S.EXPIRED, True),
    ("Approved", S.DECLINED, False),
    ("Expired", S.CLOSED, True),
    ("Declined", S.APPROVED, False),
    ("Closed", S.APPROVED, False),
    ("bogus", S.APPROVED, False),
])
def test_can_transition(src, dst, ok):
    assert can_transition(src, dst) is ok


def test_expiry_sources():
    assert set(sources_for(S.EXPIRED)) == {S.PENDING, S.APPROVED, S.NOT_APPROVED}


@pytest.mark.asyncio
async def test_declined_request_cannot_be_approved_or_closed(admin_client: AsyncClient, test_session):
    await insert_request(test_session, 1, status="Declined")
    assert (await admin_client.post(f"{P}/REQ-1/approve")).status_code == 400
    assert (await admin_client.post(
        f"{P}/REQ-1/close", json={"request_id": "REQ-1", "units_donated": 0, "donation_date": "2030-01-01"}
    )).status_code == 400


@pytest.mark.asyncio
async def test_approved_request_cannot_be_declined(admin_client: AsyncClient, test_session):
    await insert_request(test_session, 2, status="Approved")
    assert (await admin_client.post(f"{P}/REQ-2/decline")).status_code == 400


@pytest.mark.asyncio
async def test_update_status_rejects_unknown_status(test_session):
    await insert_request(test_session, 3, status="Pending")
    repo = BloodRequestRepository(test_session)
    with pytest.raises(ValueError):
        await repo.update_status("REQ-3", "Whatever")


@pytest.mark.asyncio
async def test_overdue_expiry_uses_transition_sources(test_session):
    req = await insert_request(test_session, 4, status="Pending")
    req.due_date = date(2000, 1, 1)
    await test_session.commit()
    await insert_request(test_session, 5, status="Approved")
    repo = BloodRequestRepository(test_session)
    assert await repo.expire_overdue_requests(date.today()) == 1
    rows = {r.id: r.status for r in (await test_session.execute(select(BloodRequestDetails))).scalars()}
    assert rows["REQ-4"] == "Expired" and rows["REQ-5"] == "Approved"
