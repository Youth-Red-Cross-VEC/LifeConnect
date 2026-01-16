"""
Certificate API Routes.

Endpoints for generating and managing blood donation certificates.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from pathlib import Path

from app.services.certificate_service import get_certificate_service, CertificateService
from app.services.email_service import get_email_service, EmailService
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


# =======================
# Schemas
# =======================

class CertificateRequest(BaseModel):
    """Request schema for generating a certificate."""
    
    donor_name: str = Field(..., min_length=1, max_length=100)
    donor_email: EmailStr
    donation_date: str = Field(..., description="Format: YYYY-MM-DD or human-readable")
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    location: str = Field(..., min_length=1, max_length=200)
    send_email: bool = Field(default=True, description="Send certificate via email")


class CertificateResponse(BaseModel):
    """Response schema for certificate generation."""
    
    message: str
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
):
    """
    Generate a blood donation certificate for a donor.
    
    Optionally sends the certificate via email if send_email is True.
    """
    # Generate certificate
    file_path = await cert_service.generate_certificate(
        donor_name=data.donor_name,
        donation_date=data.donation_date,
        blood_group=data.blood_group,
        location=data.location,
    )
    
    filename = Path(file_path).name
    email_sent = False
    
    # Send via email if requested
    if data.send_email:
        background_tasks.add_task(
            email_service.send_certificate,
            donor_name=data.donor_name,
            donor_email=data.donor_email,
            certificate_path=file_path,
        )
        email_sent = True
    
    return CertificateResponse(
        message=f"Certificate generated for {data.donor_name}",
        file_path=file_path,
        filename=filename,
        email_sent=email_sent,
    )


@router.get(
    "/download/{filename}",
    summary="Download a certificate",
)
async def download_certificate(
    filename: str,
    cert_service: CertificateService = Depends(get_certificate_service),
):
    """Download a generated certificate by filename."""
    file_path = await cert_service.get_certificate(filename)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=filename,
    )


@router.get(
    "/",
    response_model=CertificateListResponse,
    summary="List all certificates",
)
async def list_certificates(
    cert_service: CertificateService = Depends(get_certificate_service),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """List all generated certificates."""
    certificates = await cert_service.list_certificates()
    
    return CertificateListResponse(
        certificates=certificates,
        total=len(certificates),
    )


@router.delete(
    "/{filename}",
    response_model=SuccessResponse,
    summary="Delete a certificate",
)
async def delete_certificate(
    filename: str,
    cert_service: CertificateService = Depends(get_certificate_service),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Delete a certificate file."""
    deleted = await cert_service.delete_certificate(filename)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    return SuccessResponse(message=f"Certificate '{filename}' deleted")


@router.post(
    "/send-email",
    response_model=SuccessResponse,
    summary="Send existing certificate via email",
)
async def send_certificate_email(
    filename: str,
    donor_name: str,
    donor_email: EmailStr,
    background_tasks: BackgroundTasks,
    cert_service: CertificateService = Depends(get_certificate_service),
    email_service: EmailService = Depends(get_email_service),
):
    """Send an existing certificate via email."""
    file_path = await cert_service.get_certificate(filename)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{filename}' not found",
        )
    
    background_tasks.add_task(
        email_service.send_certificate,
        donor_name=donor_name,
        donor_email=donor_email,
        certificate_path=str(file_path),
    )
    
    return SuccessResponse(message=f"Certificate email queued for {donor_email}")
