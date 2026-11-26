"""Authenticated donor erasure requests and super administrator review."""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import Path as ApiPath
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.deps import get_current_donor, require_super_admin
from app.api.auth.utils import verify_password_async
from app.config import get_settings
from app.core.database import get_db
from app.core.rate_limiter import enforce_account_limit, limiter
from app.models.admin import AdminDetails
from app.models.donor import DonorDetail
from app.models.privacy import ErasureRequest
from app.services.audit_service import record_admin_action
from app.services.erasure_service import erase_donor, lock_donor
from app.utils.dates import utcnow

router = APIRouter(prefix="/privacy/erasure-requests", tags=["Privacy"])


class ErasureSubmission(BaseModel, extra="forbid"):
    current_password: SecretStr


class ErasureDecision(BaseModel, extra="forbid"):
    decision: Literal["approve", "reject"]


class ErasureReceipt(BaseModel):
    id: str
    status: str
    created_at: datetime
    reviewed_at: datetime | None


class ErasureReviewItem(ErasureReceipt):
    donor_id: str


@router.post("", response_model=ErasureReceipt, status_code=202)
@limiter.limit(get_settings().AUTH_RATE_LIMIT)
async def submit_erasure(
    request: Request,
    data: ErasureSubmission,
    donor: DonorDetail = Depends(get_current_donor),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    await enforce_account_limit(request, donor.email, get_settings().ACCOUNT_AUTH_RATE_LIMIT)
    locked = await lock_donor(session, donor.id)
    password = data.current_password.get_secret_value()
    if (locked is None or not locked.active_status or len(password.encode("utf-8")) > 72
            or not await verify_password_async(password, locked.password)):
        raise HTTPException(403, "Unable to verify your current password")
    existing = await session.scalar(select(ErasureRequest).where(ErasureRequest.donor_id == locked.id))
    if existing is not None and existing.status == "pending":
        return existing
    if existing is not None:
        existing.donor_id = None
        await session.flush()
    receipt = ErasureRequest(id=str(uuid4()), donor_id=locked.id)
    session.add(receipt)
    await session.flush()
    return receipt


@router.get("/mine", response_model=ErasureReceipt | None)
async def my_erasure(
    donor: DonorDetail = Depends(get_current_donor),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    return await session.scalar(select(ErasureRequest).where(ErasureRequest.donor_id == donor.id))


@router.get("", response_model=list[ErasureReviewItem])
async def pending_erasures(
    offset: int = Query(0, ge=0, le=1000000),
    limit: int = Query(50, ge=1, le=100),
    admin: AdminDetails = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    return (await session.scalars(select(ErasureRequest).where(
        ErasureRequest.status == "pending", ErasureRequest.donor_id.is_not(None),
    ).order_by(ErasureRequest.created_at, ErasureRequest.id).offset(offset).limit(limit))).all()


@router.patch("/{request_id}", response_model=ErasureReceipt)
async def review_erasure(
    request_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    data: ErasureDecision,
    admin: AdminDetails = Depends(require_super_admin),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    receipt = await session.get(ErasureRequest, request_id)
    if receipt is None:
        raise HTTPException(404, "Erasure request not found")
    donor = await lock_donor(session, receipt.donor_id) if receipt.donor_id else None
    if donor is None:
        raise HTTPException(409, "Erasure request is no longer pending")
    await session.refresh(receipt)
    if receipt.status != "pending" or receipt.donor_id != donor.id:
        raise HTTPException(409, "Erasure request is no longer pending")
    receipt.reviewed_at = utcnow()
    receipt.status = "completed" if data.decision == "approve" else "rejected"
    if data.decision == "approve":
        receipt.donor_id = None
        await erase_donor(session, donor)
    record_admin_action(session, admin.id, f"privacy.erasure_{receipt.status}", "erasure_request", receipt.id)
    return receipt
