"""
Donor API Routes.

Public endpoints for donor registration and information.
Protected endpoints require authentication (handled by partner's auth module).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
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

# Import auth dependency placeholder (partner will implement)
# from app.api.auth.deps import get_current_donor, get_current_admin

router = APIRouter(prefix="/donors", tags=["Donors"])


@router.post("/register", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def register_donor(
    data: DonorCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Register a new blood donor.
    
    This is a public endpoint - no authentication required.
    Password will be hashed before storage.
    """
    repo = DonorRepository(session)

    # Check if email already exists
    if await repo.exists_by_email(data.email):
        raise duplicate_exception("Donor", "email", data.email)

    # Hash password (partner will provide proper hashing utility)
    from hashlib import sha256
    hashed_password = sha256(data.password.encode()).hexdigest()  # TODO: Use bcrypt

    # Create related entities
    personal_details = PersonalDetails(
        id=generate_personal_details_id(),
        first_name=data.personal_details.first_name,
        last_name=data.personal_details.last_name,
        age=data.personal_details.age,
        date_of_birth=data.personal_details.date_of_birth,
        contact_number=data.personal_details.contact_number,
        secondary_contact_number=data.personal_details.secondary_contact_number,
        marital_status=data.personal_details.marital_status,
        aadhar_number=data.personal_details.aadhar_number,
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
        effective_date=date.today(),
    )

    # Create donor
    donor = DonorDetail(
        id=generate_donor_id(),
        name=data.name,
        email=data.email,
        password=hashed_password,
        blood_group=data.blood_group,
        active_status=True,
        authentication_id=generate_auth_id(),
        number_of_times_donated=0,
        personal_details_id=personal_details.id,
        address_id=address_details.id,
        disease_id=disease_details.id,
        terms_and_conditions_id=terms.id,
    )

    await repo.create(donor, personal_details, address_details, disease_details, terms)

    return DonorResponse.model_validate(donor)


@router.get("/", response_model=PaginatedResponse)
async def list_donors(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    blood_group: Optional[str] = Query(default=None),
    active_only: bool = Query(default=False),
    name_search: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Uncomment after auth
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
        name_search=name_search,
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
    session: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_donor_or_admin),  # TODO: Auth
):
    """
    Get donor details by ID.
    
    Donors can view their own profile.
    Admins can view any donor.
    """
    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    return DonorResponse.model_validate(donor)


@router.patch("/{donor_id}", response_model=DonorResponse)
async def update_donor(
    donor_id: str,
    data: DonorUpdate,
    session: AsyncSession = Depends(get_db),
    # current_donor = Depends(get_current_donor),  # TODO: Auth
):
    """
    Update donor profile.
    
    Donors can only update their own profile.
    """
    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    # Update fields if provided
    if data.name is not None:
        donor.name = data.name
    if data.blood_group is not None:
        donor.blood_group = data.blood_group
    if data.active_status is not None:
        donor.active_status = data.active_status

    await repo.update(donor)
    return DonorResponse.model_validate(donor)


@router.get("/blood-group/{blood_group}", response_model=List[DonorListResponse])
async def get_donors_by_blood_group(
    blood_group: str,
    active_only: bool = Query(default=True),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
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
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
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
    return MessageResponse(message=f"Donor {donor_id} deactivated successfully")


@router.post("/{donor_id}/activate", response_model=MessageResponse)
async def activate_donor(
    donor_id: str,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """
    Activate a donor (admin only).
    """
    repo = DonorRepository(session)
    donor = await repo.get_by_id(donor_id)

    if not donor:
        raise not_found_exception("Donor", donor_id)

    await repo.set_active_status(donor_id, True)
    return MessageResponse(message=f"Donor {donor_id} activated successfully")
