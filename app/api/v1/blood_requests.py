"""
Blood Request API Routes.

Public endpoints for creating blood requests.
Admin endpoints for managing request lifecycle.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query, BackgroundTasks
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
from app.services.certificate_service import get_certificate_service
from app.schemas.blood_request import (
    BloodRequestCreate,
    BloodRequestClose,
    BloodRequestResponse,
    BloodRequestListResponse,
)
from app.schemas.common import MessageResponse
from app.models.blood_request import BloodRequestDetails, ResponseDetails
from app.utils import generate_request_id, generate_response_id
from app.core.exceptions import not_found_exception, bad_request_exception
from app.core.request_status import BloodRequestStatus, can_transition
from app.services.audit_service import record_admin_action
from app.api.auth.deps import get_current_admin
from app.api.auth.router import enforce_recaptcha
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blood-requests", tags=["Blood Requests"])


async def _send_donation_certificates(donor_details, donation_date: str, location: str, response_id: str) -> None:
    """Generate and email one certificate per donor after a close (best effort)."""
    cert_service = get_certificate_service()
    email_service = EmailService(get_settings())
    all_sent = True
    for donor in donor_details:
        try:
            path = await cert_service.generate_certificate(
                donor_name=donor["name"],
                donation_date=donation_date,
                blood_group=donor["blood_group"],
                location=location,
            )
            sent = await email_service.send_certificate(
                donor_name=donor["name"],
                donor_email=donor["email"],
                certificate_path=path,
            )
            all_sent = all_sent and bool(sent)
        except Exception as e:
            all_sent = False
            logger.error(
                f"Certificate for donor {donor.get('id', '?')} failed: {type(e).__name__}"
            )
    # Background tasks run after the request transaction commits; open a fresh session to persist
    # the final delivery outcome.
    from app.core import database as database_module
    if database_module.db is not None:
        async with database_module.db.session() as session:
            await BloodRequestRepository(session).update_response(
                response_id, certificate_status="Sent" if all_sent else "Failed"
            )


def _status_changed() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This request was changed by someone else while you were working on it; reload and try again",
    )


@router.post("/", response_model=BloodRequestResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().BLOOD_REQUEST_RATE_LIMIT)
async def create_blood_request(
    request: Request,
    data: BloodRequestCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """
    Create a new blood donation request.

    This is a public endpoint - anyone can submit a blood request.
    Admins will be notified for approval with a single email.

    Abuse controls: a dedicated per-IP rate limit (BLOOD_REQUEST_RATE_LIMIT) and, when
    RECAPTCHA_ENFORCED=true, a valid reCAPTCHA v3 token (action "blood_request").
    """
    await enforce_recaptcha(data.recaptcha_token, "blood_request")
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
    new_request = BloodRequestDetails(
        id=generate_request_id(),
        patient_name=data.patient_name,
        blood_group=data.blood_group,
        hospital_name=hospital.hospital_name,
        hospital_id=data.hospital_id,
        contact_number=data.contact_number,
        patient_age=data.patient_age,
        due_date=data.due_date,
        request_reason=data.request_reason,
        status=BloodRequestStatus.PENDING.value,
        units_required=data.units_required,
        attendant_name=data.attendant_name,
        response_id=response.id,
    )

    await request_repo.create(new_request, response)

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

    return BloodRequestResponse.model_validate(new_request)


@router.get("/pending", response_model=List[BloodRequestListResponse])
async def get_pending_requests(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get pending blood requests (admin only)."""
    repo = BloodRequestRepository(session)
    total = await repo.count_by_status(BloodRequestStatus.PENDING)
    requests = await repo.get_pending_requests(limit=page_size, offset=(page - 1) * page_size)
    response.headers["X-Total-Count"] = str(total)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/ongoing", response_model=List[BloodRequestListResponse])
async def get_ongoing_requests(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get ongoing (approved) requests (admin only)."""
    repo = BloodRequestRepository(session)
    total = await repo.count_by_status(BloodRequestStatus.APPROVED)
    requests = await repo.get_ongoing_requests(limit=page_size, offset=(page - 1) * page_size)
    response.headers["X-Total-Count"] = str(total)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/closed", response_model=List[BloodRequestListResponse])
async def get_closed_requests(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get closed requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_closed_requests(limit=limit, offset=offset)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/expired", response_model=List[BloodRequestListResponse])
async def get_expired_requests(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get expired requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_expired_requests(limit=limit, offset=offset)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/declined", response_model=List[BloodRequestListResponse])
async def get_declined_requests(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get declined requests (admin only)."""
    repo = BloodRequestRepository(session)
    requests = await repo.get_declined_requests(limit=limit, offset=offset)
    return [BloodRequestListResponse.model_validate(r) for r in requests]


@router.get("/{request_id}", response_model=BloodRequestResponse)
async def get_blood_request(
    request_id: str,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get blood request details by ID (admin only)."""
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
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Approve a blood request and notify matching donors.
    
    Admin only endpoint.
    """
    admin_id = current_admin.id

    request_repo = BloodRequestRepository(session)
    donor_repo = DonorRepository(session)
    hospital_repo = HospitalRepository(session)

    blood_request = await request_repo.get_by_id(request_id)
    if not blood_request:
        raise not_found_exception("Blood Request", request_id)

    if not can_transition(blood_request.status, BloodRequestStatus.APPROVED):
        raise bad_request_exception(
            f"Cannot approve request with status '{blood_request.status}'"
        )

    # Update status. The check and the write are one atomic UPDATE; if another admin got there first this
    # fails before any donor is emailed.
    if not await request_repo.update_status(
        request_id, BloodRequestStatus.APPROVED, admin_id=admin_id, is_approval=True,
        expected_status=blood_request.status,
    ):
        raise _status_changed()

    # Notify matching donors. All messages go out over one SMTP connection in a single background
    # task, rather than one connection per donor.
    if send_emails:
        donors = await donor_repo.get_active_by_blood_group(blood_request.blood_group)
        hospital = await hospital_repo.get_by_id(blood_request.hospital_id)

        email_service = EmailService(get_settings())
        messages = [
            email_service.build_blood_request_notification(
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
            for donor in donors
        ]
        if messages:
            background_tasks.add_task(email_service.send_many, messages)
    else:
        donors = []

    await AdminRepository(session).increment_approved_count(admin_id)
    record_admin_action(session, admin_id, "blood_request.approve", "blood_request", request_id)
    return MessageResponse(
        message=f"Blood request {request_id} approved. {len(donors)} donors notified."
    )


@router.post("/{request_id}/decline", response_model=MessageResponse)
async def decline_blood_request(
    request_id: str,
    reason: Optional[str] = Query(default=None, max_length=255),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Decline a blood request.
    
    Admin only endpoint.
    """
    repo = BloodRequestRepository(session)
    blood_request = await repo.get_by_id(request_id)

    if not blood_request:
        raise not_found_exception("Blood Request", request_id)

    if not can_transition(blood_request.status, BloodRequestStatus.DECLINED):
        raise bad_request_exception(
            f"Cannot decline request with status '{blood_request.status}'"
        )

    if not await repo.update_status(
        request_id, BloodRequestStatus.DECLINED, expected_status=blood_request.status
    ):
        raise _status_changed()
    if reason and reason.strip():
        await repo.update_response(blood_request.response_id, report=reason.strip())
    record_admin_action(session, current_admin.id, "blood_request.decline", "blood_request", request_id)

    return MessageResponse(message=f"Blood request {request_id} declined")


@router.post("/{request_id}/close", response_model=MessageResponse)
async def close_blood_request(
    request_id: str,
    data: BloodRequestClose,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Close a blood request after donation is complete.
    
    Optionally sends certificates to donors.
    Admin only endpoint.
    """
    admin_id = current_admin.id

    request_repo = BloodRequestRepository(session)
    donor_repo = DonorRepository(session)

    blood_request = await request_repo.get_by_id(request_id)
    if not blood_request:
        raise not_found_exception("Blood Request", request_id)

    if data.request_id is not None and data.request_id != request_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="request_id must match the request ID in the URL",
        )

    if not can_transition(blood_request.status, BloodRequestStatus.CLOSED):
        raise bad_request_exception(
            f"Cannot close request with status '{blood_request.status}'"
        )

    # Validate donation data before changing anything
    donor_ids = list(dict.fromkeys(data.donor_ids))  # de-duplicate, keep order
    if data.units_donated > blood_request.units_required:
        raise bad_request_exception(
            "units_donated cannot exceed units_required "
            f"({blood_request.units_required})"
        )
    if len(donor_ids) > data.units_donated:
        raise bad_request_exception("More donors listed than units donated")
    certificate_donors = []
    for donor_id in donor_ids:
        donor = await donor_repo.get_by_id(donor_id)
        if not donor:
            raise bad_request_exception(f"Donor '{donor_id}' does not exist")
        if donor.blood_group != blood_request.blood_group:
            # Keep exact group matching. Broader compatibility (for example O- donors) is a
            # medical policy decision and must not be inferred by this workflow.
            raise bad_request_exception(
                f"Donor '{donor_id}' blood group does not match the request"
            )
        certificate_donors.append({
            "id": donor.id,
            "name": donor.name,
            "email": donor.email,
            "blood_group": donor.blood_group,
        })

    # Update request and response. Atomic: a concurrent close must not record the donation twice.
    if not await request_repo.update_status(
        request_id, BloodRequestStatus.CLOSED, admin_id=admin_id, is_close=True,
        expected_status=blood_request.status,
    ):
        raise _status_changed()

    await request_repo.update_response(
        blood_request.response_id,
        status="Completed",
        report=data.report,
        units_donated=data.units_donated,
        donation_date=data.donation_date,
        donor_ids=",".join(donor_ids) if donor_ids else None,
        certificate_status="Pending" if data.send_certificates else None,
    )

    # Update donor records
    for donor_id in donor_ids:
        await donor_repo.update_last_donated(
            donor_id, datetime.combine(data.donation_date, datetime.min.time())
        )

    await AdminRepository(session).increment_closed_count(admin_id)
    record_admin_action(
        session, admin_id, "blood_request.close", "blood_request", request_id,
        detail=f"units_donated={data.units_donated}; donors={len(donor_ids)}",
    )

    if data.send_certificates and certificate_donors:
        background_tasks.add_task(
            _send_donation_certificates,
            donor_details=certificate_donors,
            donation_date=data.donation_date.isoformat(),
            location=blood_request.hospital_name,
            response_id=blood_request.response_id,
        )
    elif data.send_certificates:
        # No donors were recorded, so no certificate delivery was required.
        await request_repo.update_response(
            blood_request.response_id, certificate_status="Sent"
        )

    return MessageResponse(
        message=f"Blood request {request_id} closed. {len(donor_ids)} donors recorded."
    )


@router.get("/stats/summary")
async def get_request_stats(
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
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
