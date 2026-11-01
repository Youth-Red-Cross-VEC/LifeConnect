from datetime import datetime, date, timezone, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.blood_request import BloodRequestCreate, BloodRequestClose


def _request_payload(due_date):
    return {
        "patient_name": "Sample Patient",
        "blood_group": "O+",
        "hospital_id": "HOSP-1",
        "contact_number": "9000000000",
        "patient_age": 40,
        "due_date": due_date,
        "units_required": 1,
    }


def test_due_date_timezone_is_normalized_to_naive_utc():
    aware = datetime(2030, 1, 1, 12, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    parsed = BloodRequestCreate.model_validate(_request_payload(aware)).due_date
    assert parsed == datetime(2030, 1, 1, 6, 30)
    assert parsed.tzinfo is None


def test_due_date_in_past_is_rejected():
    with pytest.raises(ValidationError):
        BloodRequestCreate.model_validate(_request_payload(datetime(2000, 1, 1)))


def test_donation_date_in_future_is_rejected():
    with pytest.raises(ValidationError):
        BloodRequestClose(units_donated=1, donation_date=date(2999, 1, 1))
