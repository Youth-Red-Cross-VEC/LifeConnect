# Utils package

from app.utils.dates import age_on, utcnow
from app.utils.id_generator import (
    generate_uuid,
    generate_prefixed_id,
    generate_donor_id,
    generate_admin_id,
    generate_request_id,
    generate_hospital_id,
    generate_response_id,
    generate_auth_id,
    generate_personal_details_id,
    generate_address_id,
    generate_disease_id,
    generate_terms_id,
    generate_otp,
)

__all__ = [
    "utcnow",
    "age_on",
    "generate_uuid",
    "generate_prefixed_id",
    "generate_donor_id",
    "generate_admin_id",
    "generate_request_id",
    "generate_hospital_id",
    "generate_response_id",
    "generate_auth_id",
    "generate_personal_details_id",
    "generate_address_id",
    "generate_disease_id",
    "generate_terms_id",
    "generate_otp",
]
