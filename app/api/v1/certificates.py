"""
Certificate API Routes.

Endpoints for generating and managing blood donation certificates.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import asyncio

from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.models.blood_request import ResponseDetails
from app.services.certificate_delivery import certificate_owner, deliver_certificate
from app.models.audit import AdminAuditLog
from app.models.privacy import ErasureFile
from app.repositories.blood_request import BloodRequestRepository
from typing import Optional
from pathlib import Path

from app.services.certificate_service import (
    CertificateService, get_certificate_service, read_certificate_bytes, requires_generation_record,
)
from app.services.email_service import get_email_service, EmailService
from app.schemas.common import SuccessResponse
from app.services.audit_service import record_admin_action
from app.services.erasure_service import lock_donor
from app.api.auth.deps import get_current_admin

router = APIRouter(prefix="/certificates", tags=["Certificates"])


# =======================
# Schemas
# =======================

class CertificateRequest(BaseModel):
    """Request schema for generating a certificate.

    Donor identity (name, email, blood group) is read from the database;
    the client only says WHICH donor, never who they are.
    """

    donor_id: str = Field(..., min_length=1, max_length=36)
    request_id: Optional[str] = Field(
        default=None, max_length=36,
        description="Blood request the donation belongs to; supplies the location/date defaults",
    )
    donation_date: Optional[str] = Field(
        default=None, max_length=50,
        description="Format: YYYY-MM-DD or human-readable. Defaults to the request's donation date",
    )
    location: Optional[str] = Field(default=None, max_length=200)
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
    record_admin_action(
        session, current_admin.id, "certificate.generate", "certificate", filename,
        detail=f"donor_id={data.donor_id}",
    )

    if data.send_email:
        background_tasks.add_task(
            deliver_certificate, email_service, cert_service, async_sessionmaker(session.bind),
            donor.id, current_admin.id, filename
        )

    return CertificateResponse(
        message=f"Certificate generated for {donor.name}" + (". Email queued." if data.send_email else ""),
        file_path=filename,
        filename=filename,
        email_sent=False,
    )


@router.get(
    "/download/{filename}",
    summary="Download a certificate",
)
async def download_certificate(
    filename: str,
    cert_service: CertificateService = Depends(get_certificate_service),
    current_admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """Download a generated certificate by filename (admin only)."""
    if await session.get(ErasureFile, filename):
        raise HTTPException(404, "Certificate unavailable")
    if requires_generation_record(filename) and not await certificate_owner(session, filename):
        raise HTTPException(404, "Certificate unavailable")
    path = await cert_service.get_certificate(filename)
    if path is None:
        raise HTTPException(404, "Certificate unavailable")
    try:
        contents = await asyncio.to_thread(read_certificate_bytes, path)
    except (ValueError, OSError, SyntaxError):
        raise HTTPException(404, "Certificate unavailable") from None
    return Response(contents, media_type="image/png" if path.suffix == ".png" else "text/plain",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"',
                             "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get(
    "/",
    response_model=CertificateListResponse,
    summary="List all certificates",
)
async def list_certificates(
    cert_service: CertificateService = Depends(get_certificate_service),
    current_admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """List all generated certificates."""
    certificates = await cert_service.list_certificates()
    pending = set(await session.scalars(select(ErasureFile.filename)))
    modern = [name for name in certificates if requires_generation_record(name)]
    recorded: set[str | None] = set()
    for offset in range(0, len(modern), 500):
        recorded.update(await session.scalars(select(AdminAuditLog.entity_id).where(
            AdminAuditLog.action == "certificate.generate", AdminAuditLog.entity_type == "certificate",
            AdminAuditLog.entity_id.in_(modern[offset:offset + 500]), AdminAuditLog.detail.is_not(None),
        )))
    certificates = [name for name in certificates if name not in pending and
                    (not requires_generation_record(name) or name in recorded)]
    
    return CertificateListResponse(
        certificates=certificates,
        total=len(certificates),
    )


async def remove_queued_certificate(sessions: async_sessionmaker[AsyncSession], service: CertificateService, filename: str) -> None:
    async with sessions.begin() as session:
        entry = await session.get(ErasureFile, filename, with_for_update=True)
        if entry is None:
            return
        try:
            await service.delete_certificate(filename)
        except OSError:
            return  # The scheduled cleanup retries this committed entry.
        if not service.entry_remains(filename):
            await session.delete(entry)


@router.delete(
    "/{filename}",
    response_model=SuccessResponse,
    summary="Delete a certificate",
)
async def delete_certificate(
    filename: str,
    background_tasks: BackgroundTasks,
    cert_service: CertificateService = Depends(get_certificate_service),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Delete a certificate file."""
    if await cert_service.get_certificate(filename) is None:
        raise HTTPException(404, "Certificate unavailable")
    # Use the existing durable file-removal queue. An audit rollback also rolls back removal.
    if session.get_bind().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    statement = (pg_insert(ErasureFile) if session.get_bind().dialect.name == "postgresql"
                 else sqlite_insert(ErasureFile))
    await session.execute(statement.values(filename=filename).on_conflict_do_nothing())
    background_tasks.add_task(remove_queued_certificate, async_sessionmaker(session.bind), cert_service, filename)
    record_admin_action(session, current_admin.id, "certificate.delete", "certificate", filename)
    return SuccessResponse(message="Certificate removed from access and queued for file deletion")


@router.post(
    "/send-email",
    response_model=SuccessResponse,
    summary="Send existing certificate via email",
)
async def send_certificate_email(
    filename: str,
    donor_id: str,
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

    if await certificate_owner(session, filename) != f"donor_id={donor.id}":
        raise HTTPException(404, "Certificate not found for this donor")

    file_path = None if await session.get(ErasureFile, filename) else await cert_service.get_certificate(filename)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    background_tasks.add_task(
        deliver_certificate, email_service, cert_service, async_sessionmaker(session.bind),
        donor.id, current_admin.id, filename
    )

    record_admin_action(
        session, current_admin.id, "certificate.email", "certificate", filename,
        detail=f"donor_id={donor_id}",
    )
    return SuccessResponse(message="Certificate email queued")
