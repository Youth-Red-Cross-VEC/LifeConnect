"""Shared test data builders."""

from datetime import date, datetime
from functools import lru_cache

from app.api.auth.utils import hash_password
from app.models.blood_request import BloodRequestDetails, ResponseDetails
from app.models.donor import (
    AddressDetails,
    DiseaseDetails,
    DonorDetail,
    PersonalDetails,
    TermsAndConditions,
)
from app.models.hospital import HospitalDetails


@lru_cache(maxsize=None)
def _hashed(password: str) -> str:
    """bcrypt is deliberately slow; hash each test password once per run."""
    return hash_password(password)


async def insert_donor(
    session, n: int = 1, blood_group: str = "O+", active: bool = True,
    password: str = "Secret123", email: str | None = None,
) -> DonorDetail:
    session.add_all([
        PersonalDetails(
            id=f"PD-{n}", first_name=f"Donor{n}", last_name="Test", age=30,
            date_of_birth=date(1994, 1, 1), contact_number=f"900000{n:04d}",
        ),
        AddressDetails(
            id=f"AD-{n}", address="1 Test Street", pincode="600001",
            country="India", state="TN", city="Chennai",
        ),
        DiseaseDetails(id=f"DS-{n}", name="None"),
        TermsAndConditions(id=f"TC-{n}", version="1.0", effective_date=date.today()),
    ])
    await session.flush()
    donor = DonorDetail(
        id=f"DON-{n}", name=f"Donor{n} Test", email=email or f"donor{n}@example.com",
        password=_hashed(password), blood_group=blood_group, active_status=active,
        authentication_id=f"AUTH-{n}", number_of_times_donated=0,
        personal_details_id=f"PD-{n}", address_id=f"AD-{n}", disease_id=f"DS-{n}",
        terms_and_conditions_id=f"TC-{n}",
    )
    session.add(donor)
    await session.commit()
    return donor


async def insert_request(
    session, n: int = 1, status: str = "Approved", blood_group: str = "O+",
    units_required: int = 2,
) -> BloodRequestDetails:
    hospital = await session.get(HospitalDetails, "HOSP-1")
    if hospital is None:
        session.add(HospitalDetails(
            id="HOSP-1", hospital_name="Example General Hospital", hospital_address="1 Road",
            pincode="600001", city="Chennai", state="TN", country="India",
        ))
    session.add(ResponseDetails(id=f"RESP-{n}"))
    await session.flush()
    request = BloodRequestDetails(
        id=f"REQ-{n}", patient_name="Sample Patient", blood_group=blood_group,
        hospital_name="Example General Hospital", hospital_id="HOSP-1",
        contact_number="9000200001", patient_age=40, due_date=datetime(2030, 1, 1),
        status=status, units_required=units_required, response_id=f"RESP-{n}",
    )
    session.add(request)
    await session.commit()
    return request
