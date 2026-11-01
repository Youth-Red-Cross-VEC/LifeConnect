"""
Donor API Routes.

Public endpoints for donor registration and information.
Protected endpoints require authentication (handled by partner's auth module).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.repositories.admin import AdminRepository
from app.repositories.donor import DonorRepository
from app.schemas.donor import (
    DonorCreate,
    DonorUpdate,
    DonorResponse,
    DonorListResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.models.donor import (
    DonorDetail,
    PersonalDetails,
    AddressDetails,
    DiseaseDetails,
    TermsAndConditions,
)
from app.utils import (
    generate_donor_id,
    generate_personal_details_id,
    generate_address_id,
    generate_disease_id,
    generate_terms_id,
    generate_auth_id,
)
from app.core.exceptions import duplicate_exception, not_found_exception
from app.utils.emails import normalize_email
from app.utils.dates import age_on, utcnow
from app.services.audit_service import record_admin_action
from app.services.refresh_session_service import revoke_all_for_user
from app.api.auth.deps import get_current_donor, get_current_admin, get_current_donor_or_admin

router = APIRouter(prefix="/donors", tags=["Donors"])


@router.post("/register", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def register_donor(
    data: DonorCreate,
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """
    Register a new blood donor.
    
    This is a public endpoint - no authentication required.
    Password will be hashed before storage.
    """
    repo = DonorRepository(session)

    # One identity per address, whatever the letter case, and never an address an admin already uses.
    # Both refusals read the same, so the answer does not reveal which kind of account holds the address.
    email = normalize_email(data.email)
    if await repo.exists_by_email(email) or await AdminRepository(session).exists_by_email(email):
        raise duplicate_exception("Donor", "email", data.email)

    # Age is derived from the date of birth; a client-supplied age is never trusted (it goes stale
    # within a year and can be edited to bypass the 18-65 donation window).
    age = age_on(data.personal_details.date_of_birth)
    if age is None or not (18 <= age <= 65):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Donors must be between 18 and 65 years old (checked against date_of_birth)",
        )

    # Hash password using bcrypt via passlib (canonical implementation)
    from app.api.auth.utils import hash_password_async
    hashed_password = await hash_password_async(data.password)

    # Create related entities
    personal_details = PersonalDetails(
        id=generate_personal_details_id(),
        first_name=data.personal_details.first_name,
        last_name=data.personal_details.last_name,
        age=age,
        date_of_birth=data.personal_details.date_of_birth,
        contact_number=data.personal_details.contact_number,
        secondary_contact_number=data.personal_details.secondary_contact_number,
        marital_status=data.personal_details.marital_status,
    )

    address_details = AddressDetails(
        id=generate_address_id(),
        address=data.address_details.address,
        pincode=data.address_details.pincode,
        country=data.address_details.country,
        state=data.address_details.state,
        city=data.address_details.city,
    )

    disease_details = DiseaseDetails(
        id=generate_disease_id(),
        name=data.disease_details.name,
        description=data.disease_details.description,
    )

    terms = TermsAndConditions(
        id=generate_terms_id(),
        version="1.0",
        effective_date=utcnow().date(),
    )

    # Create donor
    donor = DonorDetail(
        id=generate_donor_id(),
        name=data.name,
        email=email,
        password=hashed_password,
        blood_group=data.blood_group,
        active_status=True,
        is_available=True,
        authentication_id=generate_auth_id(),
        number_of_times_donated=0,
        personal_details_id=personal_details.id,
        address_id=address_details.id,
        disease_id=disease_details.id,
        terms_and_conditions_id=terms.id,
    )

    try:
        await repo.create(donor, personal_details, address_details, disease_details, terms)
    except IntegrityError:
        # Lost a race with a concurrent registration of the same address: the unique index caught it.
        raise duplicate_exception("Donor", "email", data.email) from None

    return DonorResponse.model_validate(donor)


@router.get("/", response_model=PaginatedResponse)
async def list_donors(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    blood_group: Optional[str] = Query(default=None),
    active_only: bool = Query(default=False),
    search: Optional[str] = Query(default=None, description="Match on donor name"),
    name_search: Optional[str] = Query(default=None, description="Deprecated alias of `search`", deprecated=True),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    List all donors with pagination and filters.
    
    Admin only endpoint (auth required).
    """
    repo = DonorRepository(session)
    offset = (page - 1) * page_size

    donors, total = await repo.get_all(
        offset=offset,
        limit=page_size,
        blood_group=blood_group,
        active_only=active_only,
        name_search=search or name_search,
    )

    return PaginatedResponse.create(
        items=[DonorListResponse.model_validate(d) for d in donors],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(
    donor_id: str,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_user = Depends(get_current_donor_or_admin),
):
    """
    Get donor details by ID.

    Access rules:
    - Admins can view any donor's full profile.
    - Donors can only view their own profile (403 if donor_id != their own ID).
    """
    # Donors can only view their own profile
    if current_user.get("user_type") == "donor" and current_user.get("user_id") != donor_id:
        from fastapi import HTTPException as _HTTPException
        raise _HTTPException(
            status_code=403,
            detail="Donors can only view their own profile",
        )

    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    return DonorResponse.model_validate(donor)


@router.patch("/{donor_id}", response_model=DonorResponse)
async def update_donor(
    donor_id: str,
    data: DonorUpdate,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_donor = Depends(get_current_donor),
):
    """
    Update donor profile.

    Donors can only update their own profile — verifies caller is the same donor.
    """
    from fastapi import HTTPException, status as http_status
    if current_donor.id != donor_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    # Update fields if provided
    # blood_group is deliberately not applied: changing it would silently alter who is notified
    # for a request. It stays immutable for donors and admins alike.
    if data.name is not None:
        donor.name = data.name
    if data.is_available is not None:
        donor.is_available = data.is_available
    if data.contact_number is not None:
        donor.personal_details.contact_number = data.contact_number
    for field in ("address", "city", "state", "pincode"):
        value = getattr(data, field)
        if value is not None:
            setattr(donor.address, field, value)

    await repo.update(donor)
    return DonorResponse.model_validate(donor)


@router.get("/blood-group/{blood_group}", response_model=list[DonorListResponse])
async def get_donors_by_blood_group(
    blood_group: str,
    active_only: bool = Query(default=True),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Get all donors with a specific blood group.
    
    Admin only endpoint.
    """
    repo = DonorRepository(session)

    if active_only:
        donors = await repo.get_active_by_blood_group(blood_group.upper())
    else:
        donors, _ = await repo.get_all(blood_group=blood_group.upper(), limit=1000)

    return [DonorListResponse.model_validate(d) for d in donors]


@router.post("/{donor_id}/deactivate", response_model=MessageResponse)
async def deactivate_donor(
    donor_id: str,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Deactivate a donor (admin only).
    
    Deactivated donors won't receive blood request notifications.
    """
    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    await repo.set_active_status(donor_id, False)
    await revoke_all_for_user(session, donor_id, "donor")
    record_admin_action(session, current_admin.id, "donor.deactivate", "donor", donor_id)
    return MessageResponse(message=f"Donor {donor_id} deactivated successfully")


@router.post("/{donor_id}/activate", response_model=MessageResponse)
async def activate_donor(
    donor_id: str,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Activate a donor (admin only).
    """
    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    await repo.set_active_status(donor_id, True)
    record_admin_action(session, current_admin.id, "donor.activate", "donor", donor_id)
    return MessageResponse(message=f"Donor {donor_id} activated successfully")
