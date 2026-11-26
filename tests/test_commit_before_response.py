"""The DB commit must happen before the response is sent, and before background tasks run.

If the commit ran after the response (FastAPI's default "request" scope for yield
dependencies), a failed commit would reach the client as a success and background emails
would go out for work that was never saved.
"""

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.auth.utils import create_access_token, hash_password
from app.core.database import get_db
from app.main import app
from app.models.admin import AdminDetails
from app.models.query import QueryTable
from app.services.email_service import EmailService
from tests.helpers import insert_donor, insert_request


@pytest.fixture
async def commit_client(test_engine):
    """Client whose get_db behaves like Database.session(), with a commit that can be made to fail."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    state = {"fail": False, "events": [], "factory": factory}

    async def override_get_db():
        async with factory() as session:
            try:
                yield session
                state["events"].append("commit")
                if state["fail"]:
                    raise RuntimeError("simulated commit failure")
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    # raise_app_exceptions=False: behave like a real server, which turns an exception into a 500
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.state = state  # type: ignore[attr-defined]
        yield client
    app.dependency_overrides.clear()


QUERY = {"user_name": "Sam", "user_email": "sam@example.com", "user_query": "How do I update my profile?"}


@pytest.mark.asyncio
async def test_commit_failure_is_reported_to_the_client_not_swallowed(commit_client):
    commit_client.state["fail"] = True
    response = await commit_client.post("/api/v1/queries/", json=QUERY)
    assert response.status_code == 500
    async with commit_client.state["factory"]() as other:
        assert (await other.execute(select(QueryTable))).scalars().all() == []


@pytest.mark.asyncio
async def test_successful_commit_still_returns_success(commit_client):
    response = await commit_client.post("/api/v1/queries/", json=QUERY)
    assert response.status_code == 201
    async with commit_client.state["factory"]() as other:
        assert len((await other.execute(select(QueryTable))).scalars().all()) == 1


async def _approve_setup(commit_client, monkeypatch):
    factory = commit_client.state["factory"]
    async with factory() as session:
        session.add(AdminDetails(
            id="ADM-1", email="admin1@example.com", password=hash_password("Secret123"),
            username="Admin One", authentication_id="AUTHADM-1", vec_registration_number="VEC-1",
            date_of_birth=date(1990, 1, 1), mobile_number="9000000000", department="IT",
            active_status="Active", approved_donation_count=0, closed_requests_count=0,
        ))
        await session.commit()
        await insert_donor(session, 1, blood_group="O+")
        await insert_request(session, 1, status="Pending", blood_group="O+")

    events = commit_client.state["events"]

    async def fake_notification(self, *args, **kwargs):
        events.append("email")

    monkeypatch.setattr(EmailService, "send_many", fake_notification)
    token = create_access_token({"sub": "ADM-1", "user_type": "admin", "email": "admin1@example.com"})
    events.clear()
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_background_email_runs_only_after_the_commit(commit_client, monkeypatch):
    headers = await _approve_setup(commit_client, monkeypatch)
    response = await commit_client.post("/api/v1/blood-requests/REQ-1/approve", headers=headers)
    assert response.status_code == 200
    assert commit_client.state["events"] == ["commit", "email"]


@pytest.mark.asyncio
async def test_no_background_email_when_the_commit_fails(commit_client, monkeypatch):
    headers = await _approve_setup(commit_client, monkeypatch)
    commit_client.state["fail"] = True
    response = await commit_client.post("/api/v1/blood-requests/REQ-1/approve", headers=headers)
    assert response.status_code == 500
    assert "email" not in commit_client.state["events"]


def test_every_get_db_dependency_uses_function_scope():
    """Guard: a plain Depends(get_db) would silently bring back commit-after-response."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "app"
    offenders = []
    for path in root.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"Depends\(\s*get_db\s*\)", line):
                offenders.append(f"{path.relative_to(root.parent)}:{number}")
    assert not offenders, offenders

async def test_certificate_generation_and_deletion_respect_commit_result(commit_client, tmp_path):
    from app.services.certificate_service import CertificateService, get_certificate_service
    from tests.helpers import insert_admin

    service = CertificateService(output_dir=str(tmp_path))
    app.dependency_overrides[get_certificate_service] = lambda: service
    async with commit_client.state["factory"]() as session:
        admin = await insert_admin(session)
        await insert_donor(session)
        token = create_access_token({"sub": admin.id, "user_type": "admin", "email": admin.email})
    headers = {"Authorization": f"Bearer {token}"}
    root = "/api/v1/certificates"
    body = {"donor_id": "DON-1", "donation_date": "2026-11-24", "send_email": False}
    commit_client.state["fail"] = True
    assert (await commit_client.post(root + "/generate", json=body, headers=headers)).status_code == 500
    orphan, = await service.list_certificates()
    commit_client.state["fail"] = False
    assert (await commit_client.get(root + "/", headers=headers)).json()["certificates"] == []
    assert (await commit_client.get(root + "/download/" + orphan, headers=headers)).status_code == 404
    generated = await commit_client.post(root + "/generate", json=body, headers=headers)
    name = generated.json()["filename"]
    commit_client.state["fail"] = True
    assert (await commit_client.delete(root + "/" + name, headers=headers)).status_code == 500
    commit_client.state["fail"] = False
    assert (await commit_client.get(root + "/download/" + name, headers=headers)).status_code == 200
    assert (await commit_client.delete(root + "/" + name, headers=headers)).status_code == 200
    assert await service.get_certificate(name) is None
