"""
Blood Request API Routes.

Public endpoints for creating blood requests.
Admin endpoints for managing request lifecycle.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.config import get_settings
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.hospital import HospitalRepository
from app.repositories.donor import DonorRepository
from app.repositories.admin import AdminRepository
from app.services.email_service import EmailService
from app.services.distance_service import DistanceService
from app.schemas.blood_request import (
    BloodRequestCreate,
    BloodRequestApprove,
    BloodRequestDecline,
    BloodRequestClose,
    BloodRequestResponse,
    BloodRequestListResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.models.blood_request import BloodRequestDetails, ResponseDetails
from app.utils import generate_request_id, generate_response_id
from app.core.exceptions import not_found_exception, bad_request_exception

# Auth dependency placeholder
# from app.api.auth.deps import get_current_admin

router = APIRouter(prefix="/blood-requests", tags=["Blood Requests"])


@router.post("/", response_model=BloodRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_blood_request(
    data: BloodRequestCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new blood donation request.
    
    This is a public endpoint - anyone can submit a blood request.
    Admins will be notified for approval.
    """
    request_repo = BloodRequestRepository(session)
    hospital_repo = HospitalRepository(session)

    # Verify hospital exists
    hospital = await hospital_repo.get_by_id(data.hospital_id)
    if not hospital:
        raise not_found_exception("Hospital", data.hospital_id)

    # Create response details (initially empty)
    response = ResponseDetails(
        id=generate_response_id(),
        status=None,
        report=None,
        units_donated=None,
    )

    # Create blood request
    request = BloodRequestDetails(
        id=generate_request_id(),
        patient_name=data.patient_name,
        blood_group=data.blood_group,
        hospital_name=hospital.hospital_name,
        hospital_id=data.hospital_id,
        contact_number=data.contact_number,
        patient_age=data.patient_age,
        due_date=data.due_date,
        request_reason=data.request_reason,
        status="Pending",
        units_required=data.units_required,
        attendant_name=data.attendant_name,
        response_id=response.id,
    )

    await request_repo.create(request, response)

    # Notify admins in background
    settings = get_settings()
    email_service = EmailService(settings)
    admin_repo = AdminRepository(session)
    admins = await admin_repo.get_all_active()
    admin_emails = [a.email for a in admins]

    if admin_emails:
        background_tasks.add_task(
            email_service.notify_admins_new_request,
            admin_emails,
            {
                "patient_name": data.patient_name,
                "blood_group": data.blood_group,
                "hospital_name": hospital.hospital_name,
                "units_required": data.units_required,
                "due_date": str(data.due_date),
            },
        )

    return BloodRequestResponse.model_validate(request)


@router.get("/pending", response_model=List[BloodRequestListResponse])
async def get_pending_requests(
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Get all pending blood requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_pending_requests()
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/ongoing", response_model=List[BloodRequestListResponse])
async def get_ongoing_requests(
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Get all ongoing (approved) requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_ongoing_requests()
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/closed", response_model=List[BloodRequestListResponse])
async def get_closed_requests(
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Get closed requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_closed_requests(limit=limit)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/expired", response_model=List[BloodRequestListResponse])
async def get_expired_requests(
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Get expired requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_expired_requests(limit=limit)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/declined", response_model=List[BloodRequestListResponse])
async def get_declined_requests(
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Get declined requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_declined_requests(limit=limit)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/{request_id}", response_model=BloodRequestResponse)
async def get_blood_request(
    request_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get blood request details by ID."""
    repo = BloodRequestRepository(session)
    request = await repo.get_by_id(request_id)

    if not request:
        raise not_found_exception("Blood Request", request_id)

    return BloodRequestResponse.model_validate(request)


@router.post("/{request_id}/approve", response_model=MessageResponse)
async def approve_blood_request(
    request_id: str,
    background_tasks: BackgroundTasks,
    send_emails: bool = Query(default=True),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """
    Approve a blood request and notify matching donors.
    
    Admin only endpoint.
    """
    admin_id = "ADM-placeholder"  # TODO: Get from current_admin

    request_repo = BloodRequestRepository(session)
    donor_repo = DonorRepository(session)
    hospital_repo = HospitalRepository(session)

    blood_request = await request_repo.get_by_id(request_id)
    if not blood_request:
        raise not_found_exception("Blood Request", request_id)

    if blood_request.status != "Pending":
        raise bad_request_exception(
            f"Cannot approve request with status '{blood_request.status}'"
        )

    # Update status
    await request_repo.update_status(
        request_id, "Approved", admin_id=admin_id, is_approval=True
    )

    # Notify matching donors
    if send_emails:
        donors = await donor_repo.get_active_by_blood_group(blood_request.blood_group)
        hospital = await hospital_repo.get_by_id(blood_request.hospital_id)

        settings = get_settings()
        email_service = EmailService(settings)

        for donor in donors:
            background_tasks.add_task(
                email_service.send_blood_request_notification,
                donor_email=donor.email,
                donor_name=donor.name,
                blood_group=blood_request.blood_group,
                patient_name=blood_request.patient_name,
                hospital_name=blood_request.hospital_name,
                hospital_address=hospital.hospital_address if hospital else "",
                contact_number=blood_request.contact_number,
                due_date=str(blood_request.due_date),
                attendant_name=blood_request.attendant_name or "",
                units_required=blood_request.units_required,
                request_reason=blood_request.request_reason or "",
                patient_age=blood_request.patient_age,
            )

    return MessageResponse(
        message=f"Blood request {request_id} approved. {len(donors) if send_emails else 0} donors notified."
    )


@router.post("/{request_id}/decline", response_model=MessageResponse)
async def decline_blood_request(
    request_id: str,
    reason: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """
    Decline a blood request.
    
    Admin only endpoint.
    """
    repo = BloodRequestRepository(session)
    blood_request = await repo.get_by_id(request_id)

    if not blood_request:
        raise not_found_exception("Blood Request", request_id)

    if blood_request.status != "Pending":
        raise bad_request_exception(
            f"Cannot decline request with status '{blood_request.status}'"
        )

    await repo.update_status(request_id, "Declined")

    return MessageResponse(message=f"Blood request {request_id} declined")


@router.post("/{request_id}/close", response_model=MessageResponse)
async def close_blood_request(
    request_id: str,
    data: BloodRequestClose,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """
    Close a blood request after donation is complete.
    
    Optionally sends certificates to donors.
    Admin only endpoint.
    """
    admin_id = "ADM-placeholder"  # TODO: Get from current_admin

    request_repo = BloodRequestRepository(session)
    donor_repo = DonorRepository(session)

    blood_request = await request_repo.get_by_id(request_id)
    if not blood_request:
        raise not_found_exception("Blood Request", request_id)

    if blood_request.status not in ["Approved", "Expired"]:
        raise bad_request_exception(
            f"Cannot close request with status '{blood_request.status}'"
        )

    # Update request and response
    await request_repo.update_status(
        request_id, "Closed", admin_id=admin_id, is_close=True
    )

    await request_repo.update_response(
        blood_request.response_id,
        status="Completed",
        report=data.report,
        units_donated=data.units_donated,
        donation_date=data.donation_date,
        donor_ids=",".join(data.donor_ids) if data.donor_ids else None,
        certificate_status="Pending" if data.send_certificates else None,
    )

    # Update donor records
    for donor_id in data.donor_ids:
        await donor_repo.update_last_donated(
            donor_id, datetime.combine(data.donation_date, datetime.min.time())
        )

    # TODO: Send certificates in background
    # if data.send_certificates:
    #     for donor_id in data.donor_ids:
    #         donor = await donor_repo.get_by_id(donor_id)
    #         if donor:
    #             background_tasks.add_task(generate_and_send_certificate, donor, blood_request)

    return MessageResponse(
        message=f"Blood request {request_id} closed. {len(data.donor_ids)} donors recorded."
    )


@router.get("/stats/summary")
async def get_request_stats(
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Get blood request statistics (admin only)."""
    repo = BloodRequestRepository(session)

    status_stats = await repo.get_status_stats()
    blood_group_stats = await repo.get_blood_group_stats()

    return {
        "by_status": status_stats,
        "by_blood_group": blood_group_stats,
        "total": sum(status_stats.values()),
    }
