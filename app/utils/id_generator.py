import uuid
from datetime import datetime


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def generate_prefixed_id(prefix: str) -> str:
    """
    Generate an ID with a prefix.
    
    Example: generate_prefixed_id("DON") -> "DON-abc12345"
    """
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}-{short_uuid}"


def generate_donor_id() -> str:
    """Generate donor ID."""
    return generate_prefixed_id("DON")


def generate_admin_id() -> str:
    """Generate admin ID."""
    return generate_prefixed_id("ADM")


def generate_request_id() -> str:
    """Generate blood request ID."""
    return generate_prefixed_id("REQ")


def generate_hospital_id() -> str:
    """Generate hospital ID."""
    return generate_prefixed_id("HSP")


def generate_response_id() -> str:
    """Generate response ID."""
    return generate_prefixed_id("RSP")


def generate_auth_id() -> str:
    """Generate authentication ID."""
    return generate_prefixed_id("AUTH")


def generate_personal_details_id() -> str:
    """Generate personal details ID."""
    return generate_prefixed_id("PD")


def generate_address_id() -> str:
    """Generate address ID."""
    return generate_prefixed_id("ADDR")


def generate_disease_id() -> str:
    """Generate disease details ID."""
    return generate_prefixed_id("DIS")


def generate_terms_id() -> str:
    """Generate terms and conditions ID."""
    return generate_prefixed_id("TNC")


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    import secrets
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
