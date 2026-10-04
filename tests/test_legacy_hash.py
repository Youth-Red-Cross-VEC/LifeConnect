"""Legacy scrypt (werkzeug format) password hashes must verify and upgrade to bcrypt."""

import hashlib
from datetime import date

import pytest
from httpx import AsyncClient

from app.api.auth.utils import needs_rehash, verify_password
from app.models.admin import AdminDetails
from app.models.donor import (
    AddressDetails,
    DiseaseDetails,
    DonorDetail,
    PersonalDetails,
    TermsAndConditions,
)


def make_scrypt_hash(password: str, salt: str = "XIjoEBWPpgO1inbw", n=32768, r=8, p=1) -> str:
    digest = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=n, r=r, p=p, maxmem=132 * n * r * p
    ).hex()
    return f"scrypt:{n}:{r}:{p}${salt}${digest}"


class TestLegacyScryptVerification:
    def test_correct_password_verifies(self):
        assert verify_password("Secret123", make_scrypt_hash("Secret123"))

    def test_wrong_password_rejected(self):
        assert not verify_password("Wrong123", make_scrypt_hash("Secret123"))

    def test_malformed_hash_rejected(self):
        assert not verify_password("x", "scrypt:abc:8:1$salt$zz")
        assert not verify_password("x", "scrypt:32768:8:1$onlytwo")

    def test_scrypt_needs_rehash_bcrypt_does_not(self):
        assert needs_rehash(make_scrypt_hash("Secret123"))
        from app.api.auth.utils import hash_password

        assert not needs_rehash(hash_password("Secret123"))


async def _insert_legacy_donor(session, password_hash: str) -> DonorDetail:
    personal = PersonalDetails(
        id="PD-1", first_name="Legacy", last_name="User", age=30,
        date_of_birth=date(1994, 1, 1), contact_number="9000000000",
    )
    address = AddressDetails(
        id="AD-1", address="1 Test Street", pincode="600001",
        country="India", state="TN", city="Chennai",
    )
    disease = DiseaseDetails(id="DS-1", name="None")
    terms = TermsAndConditions(id="TC-1", version="1.0", effective_date=date.today())
    donor = DonorDetail(
        id="DON-legacy", name="Legacy User", email="legacy@example.com",
        password=password_hash, blood_group="O+", active_status=True,
        authentication_id="AUTH-legacy", number_of_times_donated=0,
        personal_details_id="PD-1", address_id="AD-1", disease_id="DS-1",
        terms_and_conditions_id="TC-1",
    )
    session.add_all([personal, address, disease, terms])
    await session.flush()
    session.add(donor)
    await session.commit()
    return donor


@pytest.mark.asyncio
async def test_donor_login_upgrades_scrypt_hash_to_bcrypt(client: AsyncClient, test_session):
    donor = await _insert_legacy_donor(test_session, make_scrypt_hash("Secret123"))

    response = await client.post(
        "/api/v1/auth/donor/login",
        json={"email": "legacy@example.com", "password": "Secret123"},
    )
    assert response.status_code == 200

    await test_session.refresh(donor)
    assert donor.password.startswith("$2")
    assert verify_password("Secret123", donor.password)


@pytest.mark.asyncio
async def test_admin_login_upgrades_scrypt_hash_to_bcrypt(client: AsyncClient, test_session):
    admin = AdminDetails(
        id="ADM-legacy", email="legacyadmin@example.com",
        password=make_scrypt_hash("Secret123"), username="Legacy Admin",
        authentication_id="AUTHADM-legacy", vec_registration_number="VEC-LEG",
        date_of_birth=date(1990, 1, 1), mobile_number="9000000001", department="IT",
        active_status="Active", approved_donation_count=0, closed_requests_count=0,
    )
    test_session.add(admin)
    await test_session.commit()

    response = await client.post(
        "/api/v1/auth/admin/login",
        json={"email": "legacyadmin@example.com", "password": "Secret123"},
    )
    assert response.status_code == 200

    await test_session.refresh(admin)
    assert admin.password.startswith("$2")


@pytest.mark.asyncio
async def test_wrong_password_does_not_change_hash(client: AsyncClient, test_session):
    legacy = make_scrypt_hash("Secret123")
    donor = await _insert_legacy_donor(test_session, legacy)

    response = await client.post(
        "/api/v1/auth/donor/login",
        json={"email": "legacy@example.com", "password": "Nope12345"},
    )
    assert response.status_code == 401
    await test_session.refresh(donor)
    assert donor.password == legacy
