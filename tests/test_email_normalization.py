"""B8: donor emails are case-insensitive, and a donor cannot register with an admin's address."""

import importlib

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.donor import DonorDetail
from app.repositories.donor import DonorRepository
from tests.helpers import insert_admin, insert_donor, registration_payload

auth_router = importlib.import_module("app.api.auth.router")

REGISTER = "/api/v1/donors/register"


async def _emails(session) -> list[str]:
    return [e for (e,) in (await session.execute(select(DonorDetail.email).order_by(DonorDetail.email))).all()]


@pytest.mark.asyncio
async def test_registration_stores_the_email_lowercased(client: AsyncClient, test_session):
    r = await client.post(REGISTER, json=registration_payload("Mixed.Case@Example.COM"))
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "mixed.case@example.com"
    assert await _emails(test_session) == ["mixed.case@example.com"]


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["mixed.case@example.com", "MIXED.CASE@EXAMPLE.COM", "Mixed.Case@Example.com"])
async def test_a_case_variant_of_a_registered_email_is_a_duplicate(client: AsyncClient, test_session, variant):
    assert (await client.post(REGISTER, json=registration_payload("mixed.case@example.com"))).status_code == 201
    r = await client.post(REGISTER, json=registration_payload(variant))
    assert r.status_code == 409
    assert len(await _emails(test_session)) == 1


@pytest.mark.asyncio
async def test_a_case_variant_of_a_legacy_mixed_case_row_is_a_duplicate(client: AsyncClient, test_session):
    await insert_donor(test_session, 1, email="Legacy.User@Example.com")  # stored before normalization existed
    r = await client.post(REGISTER, json=registration_payload("legacy.user@example.com"))
    assert r.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("typed", ["donor1@example.com", "DONOR1@EXAMPLE.COM", " Donor1@Example.com "])
async def test_login_ignores_email_case_and_padding(client: AsyncClient, test_session, typed):
    await insert_donor(test_session, 1)
    r = await client.post("/api/v1/auth/donor/login", json={"email": typed.strip(), "password": "Secret123"})
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_login_finds_a_legacy_mixed_case_account(client: AsyncClient, test_session):
    await insert_donor(test_session, 1, email="Legacy.User@Example.com")
    for typed in ("legacy.user@example.com", "LEGACY.USER@EXAMPLE.COM", "Legacy.User@Example.com"):
        r = await client.post("/api/v1/auth/donor/login", json={"email": typed, "password": "Secret123"})
        assert r.status_code == 200, (typed, r.text)


class _Mailer:
    def __init__(self):
        self.sent = []

    async def send_otp_email(self, email, otp, name):
        self.sent.append(email)
        return True


@pytest.mark.asyncio
async def test_password_reset_request_finds_the_account_in_any_case(client: AsyncClient, test_session, monkeypatch):
    await insert_donor(test_session, 1)
    mailer = _Mailer()
    monkeypatch.setattr(auth_router, "get_email_service", lambda: mailer)

    r = await client.post("/api/v1/auth/donor/password-reset/request", json={"email": "DONOR1@Example.com"})

    assert r.status_code == 200
    assert mailer.sent == ["donor1@example.com"]


@pytest.mark.asyncio
async def test_repository_lookups_are_case_insensitive(test_session):
    await insert_donor(test_session, 1, email="Legacy.User@Example.com")
    repo = DonorRepository(test_session)
    assert await repo.exists_by_email("LEGACY.USER@example.com") is True
    assert (await repo.get_by_email("legacy.user@EXAMPLE.COM")).id == "DON-1"
    assert await repo.exists_by_email("someone.else@example.com") is False


# ------------------------------------------------------------------ admins' addresses

@pytest.mark.asyncio
@pytest.mark.parametrize("typed", ["admin1@example.com", "ADMIN1@Example.com"])
async def test_a_donor_cannot_register_with_an_admins_email(client: AsyncClient, test_session, typed):
    await insert_admin(test_session, 1)

    r = await client.post(REGISTER, json=registration_payload(typed))

    assert r.status_code == 409
    assert await _emails(test_session) == []


@pytest.mark.asyncio
async def test_admin_email_and_donor_email_collisions_look_the_same(client: AsyncClient, test_session):
    """The refusal must not reveal whether the address belongs to an admin or to another donor."""
    await insert_admin(test_session, 1)
    await insert_donor(test_session, 1)

    as_admin = await client.post(REGISTER, json=registration_payload("admin1@example.com"))
    as_donor = await client.post(REGISTER, json=registration_payload("donor1@example.com"))

    assert as_admin.status_code == as_donor.status_code == 409
    strip = lambda body, who: body["detail"].replace(who, "<email>")
    assert strip(as_admin.json(), "admin1@example.com") == strip(as_donor.json(), "donor1@example.com")


@pytest.mark.asyncio
async def test_admin_login_ignores_email_case(client: AsyncClient, test_session):
    await insert_admin(test_session, 1)
    r = await client.post("/api/v1/auth/admin/login", json={"email": "ADMIN1@EXAMPLE.COM", "password": "Secret123"})
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_losing_a_registration_race_is_a_409_not_a_500(client: AsyncClient, test_session, monkeypatch):
    """Two requests pass the duplicate check together; the unique index must turn the loser into a 409."""
    await insert_donor(test_session, 1, email="Racer@Example.com")
    async def never_seen(self, email):
        return False
    monkeypatch.setattr(DonorRepository, "exists_by_email", never_seen)

    r = await client.post(REGISTER, json=registration_payload("racer@example.com"))

    assert r.status_code == 409
