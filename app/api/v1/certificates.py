"""
Certificate API Routes.

Endpoints for generating and managing blood donation certificates.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path as ApiPath
import asyncio
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.blood_request import ResponseDetails
from app.models.privacy import ErasureFile
from app.models.audit import AdminAuditLog
from app.repositories.blood_request import BloodRequestRepository
from typing import Annotated, Optional
from pathlib import Path

from app.services.certificate_service import get_certificate_service, CertificateService, read_certificate_bytes
from app.services.email_service import get_email_service, EmailService
from app.schemas.validation import RecordId, SingleLine
from app.schemas.common import SuccessResponse
from app.services.audit_service import record_admin_action
from app.services.erasure_service import lock_donor
from app.api.auth.deps import get_current_admin

router = APIRouter(prefix="/certificates", tags=["Certificates"])


async def _email_then_delete(email_service: EmailService, cert_service: CertificateService,
                             donor_id: str, donor_name: str, donor_email: str, path: str) -> bool:
    from app.core import database

    async def send(name: str, email: str) -> bool:
        sent = await email_service.send_certificate(
            donor_name=name, donor_email=email, certificate_path=path
        )
        if sent:
            await cert_service.delete_certificate(Path(path).name)
        return sent

    if database.db is None:
        return await send(donor_name, donor_email)
    async with database.db.session() as session:
        donor = await lock_donor(session, donor_id)
        if donor is None or await session.get(ErasureFile, Path(path).name):
            return False
        return await send(donor.name, donor.email)


# =======================
# Schemas
# =======================

class CertificateRequest(BaseModel, extra="forbid"):
    """Request schema for generating a certificate.

    Donor identity (name, email, blood group) is read from the database;
    the client only says WHICH donor, never who they are.
    """

    donor_id: RecordId = Field(..., min_length=1, max_length=36)
    request_id: Optional[RecordId] = Field(
        default=None, max_length=36,
        description="Blood request the donation belongs to; supplies the location/date defaults",
    )
    donation_date: Optional[SingleLine] = Field(
        default=None, max_length=50,
        description="Format: YYYY-MM-DD or human-readable. Defaults to the request's donation date",
    )
    location: Optional[SingleLine] = Field(default=None, max_length=200)
    send_email: bool = Field(default=True, description="Send certificate via email")


class CertificateResponse(BaseModel):
    """Response schema for certificate generation."""
    
    message: str
    # Just the file name: the path /certificates/download/{filename} is how clients fetch it,
    # and the server's absolute path must not leak. Use the `filename` field for the same value.
    file_path: str
    filename: str
    email_sent: bool = False


class CertificateListResponse(BaseModel):
    """Response schema for listing certificates."""
    
    certificates: list[str]
    total: int


# =======================
# Endpoints
# =======================

@router.post(
    "/generate",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a donation certificate",
)
async def generate_certificate(
    data: CertificateRequest,
    background_tasks: BackgroundTasks,
    cert_service: CertificateService = Depends(get_certificate_service),
    email_service: EmailService = Depends(get_email_service),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Generate a blood donation certificate for a registered donor (admin only).

    Name, email and blood group come from the donor record, never from the client.
    Optionally sends the certificate to the donor's registered email.
    """
    donor = await lock_donor(session, data.donor_id)
    if not donor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")

    donation_date = data.donation_date
    location = data.location
    if data.request_id:
        blood_request = await BloodRequestRepository(session).get_by_id(data.request_id)
        if not blood_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Blood request not found"
            )
        location = location or blood_request.hospital_name
        response_details = await session.get(ResponseDetails, blood_request.response_id)
        if not donation_date and response_details and response_details.donation_date:
            donation_date = response_details.donation_date.isoformat()

    if not donation_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="donation_date is required unless request_id has a recorded donation date",
        )

    file_path = await cert_service.generate_certificate(
        donor_name=donor.name,
        donation_date=donation_date,
        blood_group=donor.blood_group,
        location=location or "Not specified",
    )

    filename = Path(file_path).name
    email_sent = False
    record_admin_action(
        session, current_admin.id, "certificate.generate", "certificate", filename,
        detail=f"donor_id={data.donor_id}",
    )

    if data.send_email:
        background_tasks.add_task(
            _email_then_delete, email_service, cert_service, donor.id, donor.name, donor.email, file_path
        )
        email_sent = True

    return CertificateResponse(
        message=f"Certificate generated for {donor.name}",
        file_path=filename,
        filename=filename,
        email_sent=email_sent,
    )


@router.get(
    "/download/{filename}",
    summary="Download a certificate",
)
async def download_certificate(
    filename: Annotated[str, ApiPath(max_length=180)],
    cert_service: CertificateService = Depends(get_certificate_service),
    current_admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """Download a generated certificate by filename (admin only)."""
    file_path = None if await session.get(ErasureFile, filename) else await cert_service.get_certificate(filename)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    try:
        contents = await asyncio.to_thread(read_certificate_bytes, file_path)
    except (ValueError, OSError, SyntaxError):
        raise HTTPException(404, "Certificate unavailable") from None
    return Response(
        contents, media_type="image/png" if file_path.suffix == ".png" else "text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "private, no-store"},
    )


@router.get(
    "/",
    response_model=CertificateListResponse,
    summary="List all certificates",
)
async def list_certificates(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0, le=1000000),
    cert_service: CertificateService = Depends(get_certificate_service),
    current_admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """List all generated certificates."""
    certificates = await cert_service.list_certificates()
    pending = set(await session.scalars(select(ErasureFile.filename)))
    certificates = [name for name in certificates if name not in pending]
    
    return CertificateListResponse(
        certificates=certificates[offset:offset + limit],
        total=len(certificates),
    )


@router.delete(
    "/{filename}",
    response_model=SuccessResponse,
    summary="Delete a certificate",
)
async def delete_certificate(
    filename: Annotated[str, ApiPath(max_length=180)],
    cert_service: CertificateService = Depends(get_certificate_service),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Delete a certificate file."""
    deleted = await cert_service.delete_certificate(filename)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    record_admin_action(session, current_admin.id, "certificate.delete", "certificate", filename)
    return SuccessResponse(message=f"Certificate '{filename}' deleted")


@router.post(
    "/send-email",
    response_model=SuccessResponse,
    summary="Send existing certificate via email",
)
async def send_certificate_email(
    filename: Annotated[str, Query(min_length=1, max_length=180)],
    donor_id: Annotated[str, Query(min_length=1, max_length=36)],
    background_tasks: BackgroundTasks,
    cert_service: CertificateService = Depends(get_certificate_service),
    email_service: EmailService = Depends(get_email_service),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Send an existing certificate to a registered donor (admin only).

    Recipient name and email are read from the donor record, never from the client.
    """
    donor = await lock_donor(session, donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    owner = await session.scalar(
        select(AdminAuditLog.detail).where(
            AdminAuditLog.entity_type == "certificate", AdminAuditLog.entity_id == filename,
            AdminAuditLog.action == "certificate.generate",
        ).order_by(AdminAuditLog.id.desc()).limit(1)
    )
    if owner != f"donor_id={donor.id}":
        raise HTTPException(404, "Certificate not found for this donor")

    file_path = None if await session.get(ErasureFile, filename) else await cert_service.get_certificate(filename)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    background_tasks.add_task(
        _email_then_delete, email_service, cert_service, donor.id, donor.name, donor.email, str(file_path)
    )

    record_admin_action(
        session, current_admin.id, "certificate.email", "certificate", filename,
        detail=f"donor_id={donor_id}",
    )
    return SuccessResponse(message="Certificate email queued")
