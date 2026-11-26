"""Resolve the certificate recipient and record SMTP acceptance under the donor lock."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import AdminAuditLog
from app.models.privacy import ErasureFile
from app.services.audit_service import record_admin_action
from app.services.certificate_service import CertificateService
from app.services.email_service import EmailService
from app.services.erasure_service import lock_donor

logger = logging.getLogger(__name__)


async def certificate_owner(session: AsyncSession, filename: str) -> str | None:
    return await session.scalar(select(AdminAuditLog.detail).where(
        AdminAuditLog.entity_type == "certificate", AdminAuditLog.entity_id == filename,
        AdminAuditLog.action == "certificate.generate",
    ).order_by(AdminAuditLog.id.desc()).limit(1))


async def deliver_certificate(email_service: EmailService, cert_service: CertificateService,
                              sessions: async_sessionmaker[AsyncSession], donor_id: str, admin_id: str, filename: str) -> bool:
    async with sessions.begin() as session:
        donor = await lock_donor(session, donor_id)
        pending_removal = await session.get(ErasureFile, filename)
        if donor is None or pending_removal is not None:
            return False
        if await certificate_owner(session, filename) != f"donor_id={donor_id}":
            return False
        accepted = await session.scalar(select(AdminAuditLog.id).where(
            AdminAuditLog.entity_type == "certificate", AdminAuditLog.entity_id == filename,
            AdminAuditLog.action == "certificate.accepted",
        ).limit(1))
        if accepted:
            return True
        path = await cert_service.get_certificate(filename)
        if not path or not await email_service.send_certificate(donor.name, donor.email, str(path)):
            return False
        record_admin_action(session, admin_id, "certificate.accepted", "certificate", filename,
                            detail=f"donor_id={donor_id}")
    # Record relay acceptance before cleanup. A retained file cannot trigger a second submission.
    try:
        await cert_service.delete_certificate(filename)
    except OSError as exc:
        logger.warning("Accepted certificate cleanup failed type=%s", type(exc).__name__)
    return True
