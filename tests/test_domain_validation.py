"""Domain-validation regression cases using synthetic accounts and API payloads."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.admin import AdminUpdate
from app.schemas.blood_request import BloodRequestCreate
from app.schemas.donor import DonorCreate, DonorUpdate
from tests.helpers import registration_payload


def blood_request(**changes):
    return dict({
        "hospital_id": "HOSP-1", "patient_name": "Example", "patient_age": 24,
        "blood_group": "o+", "due_date": (date.today() + timedelta(days=2)).isoformat(),
        "units_required": 1, "contact_number": "9000000000",
    }, **changes)


def test_valid_registration_preserves_unicode_credentials_and_postal_code():
    body = registration_payload("donor@example.com", " Secret123 ")
    body.update(name="  குமார் O’Neil  ", blood_group=" ab- ")
    body["address_details"]["pincode"] = " 01234 "
    body["personal_details"]["contact_number"] = "+91 (90000) 00000"
    donor = DonorCreate.model_validate(body)
    assert donor.name == "குமார் O’Neil" and donor.password == " Secret123 "
    assert donor.blood_group == "AB-" and donor.address_details.pincode == "01234"
    assert donor.personal_details.contact_number == "+919000000000"


@pytest.mark.parametrize("value", ["letters1234", "9000000000\n", "12+", "1" * 17, "123456789"])
def test_phone_validation_is_shared(value):
    for model, body in ((AdminUpdate, {"mobile_number": value}), (DonorUpdate, {"contact_number": value}),
                        (BloodRequestCreate, blood_request(contact_number=value))):
        with pytest.raises(ValidationError):
            model.model_validate(body)


def test_phone_storage_boundaries():
    assert DonorUpdate(contact_number="+" + "1"*14).contact_number == "+" + "1"*14
    with pytest.raises(ValidationError):
        DonorUpdate(contact_number="+" + "1"*15)
    assert AdminUpdate(mobile_number="+" + "1"*15).mobile_number == "+" + "1"*15


@pytest.mark.parametrize(("field", "value"), [
    ("enrollment_code", "１２３４５６"),
    ("enrollment_code", "12345"),
    ("date_of_birth", (date.today() + timedelta(days=1)).isoformat()),
    ("pincode", "12/345"),
])
def test_registration_reports_invalid_domain_field(field, value):
    body = registration_payload("donor@example.com", "Valid1234")
    if field == "pincode":
        body["address_details"][field] = value
    elif field == "date_of_birth":
        body["personal_details"][field] = value
    else:
        body[field] = value
    with pytest.raises(ValidationError) as error:
        DonorCreate.model_validate(body)
    assert any(item["loc"][-1] == field for item in error.value.errors())


@pytest.mark.parametrize("changes", [
    {"patient_name": "  "}, {"patient_name": "Two\nLines"}, {"hospital_id": "  "},
    {"due_date": 9999999999}, {"blood_group": "A++"}, {"units_required": True},
])
def test_blood_request_rejects_invalid_fields(changes):
    with pytest.raises(ValidationError):
        BloodRequestCreate.model_validate(blood_request(**changes))


async def test_invalid_contact_never_becomes_a_database_lookup(client):
    response = await client.post("/api/v1/blood-requests/", json=blood_request(contact_number="PRIVATE-NUMBER"))
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "contact_number"]
    assert "PRIVATE-NUMBER" not in response.text


@pytest.mark.parametrize("key", ["__proto__", "constructor", "prototype"])
async def test_nested_reserved_keys_rejected(client, key):
    rsp = await client.post("/api/v1/queries/", json={"user_query": {key: {"value": 1}}})
    assert rsp.status_code == 400


async def test_query_preserves_markup_as_literal_text(client):
    text = "  A <b>question</b> & answer\n第二行  "
    base = {"user_email": "test@example.com", "user_name": " Sam ", "user_query": text}
    r = await client.post("/api/v1/queries/", json=base)
    assert r.status_code == 201
    assert r.json()["user_query"] == text.strip() and r.json()["user_name"] == "Sam"
    assert (await client.post("/api/v1/queries/", json={**base, "user_query": " " * 12})).status_code == 422
