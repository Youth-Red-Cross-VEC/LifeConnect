"""B12: a status change is one atomic compare-and-swap, so concurrent admins cannot double-apply it.

A race needs two requests that both read the request as "Pending"/"Approved" before either writes. Tests
reproduce the loser deterministically: the second call is handed the stale snapshot the first call saw
(exactly what a concurrent request would have read), while the database already holds the new status.
"""

from datetime import date
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy import inspect, select

from app.core.request_status import BloodRequestStatus
from app.models.blood_request import BloodRequestDetails
from app.models.donor import DonorDetail
from app.repositories.blood_request import BloodRequestRepository
from app.services.email_service import EmailService
from tests.helpers import insert_donor, insert_request


@pytest.fixture
def stale_reads(monkeypatch):
    """Record the first read of a request; replay() makes later reads return that stale snapshot."""
    real = BloodRequestRepository.get_by_id
    state = {"snapshot": None, "replay": False}

    async def get_by_id(self, request_id):
        if state["replay"] and state["snapshot"] is not None:
            return state["snapshot"]
        found = await real(self, request_id)
        if found is not None and state["snapshot"] is None:
            columns = inspect(found).mapper.column_attrs
            state["snapshot"] = SimpleNamespace(**{c.key: getattr(found, c.key) for c in columns})
        return found

    monkeypatch.setattr(BloodRequestRepository, "get_by_id", get_by_id)
    return SimpleNamespace(replay=lambda: state.update(replay=True))


@pytest.fixture
def donor_emails(monkeypatch):
    sent = []

    async def fake(self, messages):
        sent.extend(message["to"] for message in messages)

    monkeypatch.setattr(EmailService, "send_many", fake)
    return sent


async def _status(session, request_id="REQ-1") -> str:
    return (await session.execute(
        select(BloodRequestDetails.status).where(BloodRequestDetails.id == request_id)
    )).scalar_one()


# ------------------------------------------------------------------ repository

@pytest.mark.asyncio
async def test_update_status_only_applies_from_the_expected_status(test_session):
    await insert_request(test_session, 1, status="Pending")
    repo = BloodRequestRepository(test_session)

    assert await repo.update_status("REQ-1", BloodRequestStatus.APPROVED, expected_status="Approved") is False
    assert await _status(test_session) == "Pending"

    assert await repo.update_status("REQ-1", BloodRequestStatus.APPROVED, expected_status="Pending") is True
    assert await _status(test_session) == "Approved"


@pytest.mark.asyncio
async def test_update_status_without_an_expected_status_still_refuses_an_impossible_move(test_session):
    await insert_request(test_session, 1, status="Declined")
    repo = BloodRequestRepository(test_session)

    assert await repo.update_status("REQ-1", BloodRequestStatus.APPROVED) is False
    assert await _status(test_session) == "Declined"


# ------------------------------------------------------------------ approve

@pytest.mark.asyncio
async def test_concurrent_approve_notifies_donors_once(admin_client: AsyncClient, test_session, stale_reads, donor_emails):
    await insert_donor(test_session, 1, blood_group="O+")
    await insert_request(test_session, 1, status="Pending", blood_group="O+")

    first = await admin_client.post("/api/v1/blood-requests/REQ-1/approve")
    assert first.status_code == 200
    stale_reads.replay()
    second = await admin_client.post("/api/v1/blood-requests/REQ-1/approve")

    assert second.status_code == 409
    assert donor_emails == ["donor1@example.com"], "the loser must not queue a second round of emails"


@pytest.mark.asyncio
async def test_approve_racing_a_decline_leaves_the_first_decision(admin_client: AsyncClient, test_session, stale_reads, donor_emails):
    await insert_donor(test_session, 1, blood_group="O+")
    await insert_request(test_session, 1, status="Pending", blood_group="O+")

    assert (await admin_client.post("/api/v1/blood-requests/REQ-1/approve")).status_code == 200
    stale_reads.replay()
    late_decline = await admin_client.post("/api/v1/blood-requests/REQ-1/decline")

    assert late_decline.status_code == 409
    assert await _status(test_session) == "Approved"


# ------------------------------------------------------------------ close

def _close_body(donor_id: str = "DON-1") -> dict:
    return {
        "request_id": "REQ-1", "units_donated": 1, "donation_date": date.today().isoformat(),
        "donor_ids": [donor_id], "send_certificates": False,
    }


@pytest.mark.asyncio
async def test_concurrent_close_counts_the_donation_once(admin_client: AsyncClient, test_session, stale_reads):
    await insert_donor(test_session, 1, blood_group="O+")
    await insert_request(test_session, 1, status="Approved", blood_group="O+")

    first = await admin_client.post("/api/v1/blood-requests/REQ-1/close", json=_close_body())
    assert first.status_code == 200
    stale_reads.replay()
    second = await admin_client.post("/api/v1/blood-requests/REQ-1/close", json=_close_body())

    assert second.status_code == 409
    times = (await test_session.execute(
        select(DonorDetail.number_of_times_donated).where(DonorDetail.id == "DON-1")
    )).scalar_one()
    assert times == 1, "the loser must not increment the donor's count again"


@pytest.mark.asyncio
async def test_close_rejects_body_request_id_that_differs_from_path(admin_client: AsyncClient, test_session):
    await insert_request(test_session, 1, status="Approved", blood_group="O+")
    body = _close_body()
    body["request_id"] = "REQ-other"
    response = await admin_client.post("/api/v1/blood-requests/REQ-1/close", json=body)
    assert response.status_code == 400


# ------------------------------------------------------------------ the ordinary paths still behave

@pytest.mark.asyncio
async def test_a_plain_second_approve_returns_conflict(admin_client: AsyncClient, test_session, donor_emails):
    await insert_request(test_session, 1, status="Pending")
    assert (await admin_client.post("/api/v1/blood-requests/REQ-1/approve")).status_code == 200
    again = await admin_client.post("/api/v1/blood-requests/REQ-1/approve")
    assert again.status_code == 409
    assert "changed" in again.json()["detail"].lower()
