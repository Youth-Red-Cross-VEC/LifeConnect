"""Transactional donor erasure. Files use a retry queue because they cannot join a DB transaction."""

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.models.audit import AdminAuditLog
from app.models.blood_request import ResponseDetails
from app.models.donor import (
    AddressDetails,
    AuthenticationDetailsDonor,
    DiseaseDetails,
    DonorDetail,
    PersonalDetails,
)
from app.models.otp import OtpCode, OtpFailureWindow
from app.models.privacy import ErasureFile
from app.models.query import QueryTable
from app.models.refresh_session import RefreshSession
from app.services.otp_service import PURPOSE_DONOR_ENROLLMENT, PURPOSE_DONOR_RESET


async def lock_donor(session: AsyncSession, donor_id: str) -> DonorDetail | None:
    # The joined optional relationships must be excluded from PostgreSQL's row lock.
    query = (select(DonorDetail).options(lazyload("*")).where(DonorDetail.id == donor_id)
             .with_for_update(of=DonorDetail).execution_options(populate_existing=True))
    return await session.scalar(query)


async def erase_donor(session: AsyncSession, donor: DonorDetail) -> None:
    donor_id, email = donor.id, donor.email.lower()
    await session.execute(delete(RefreshSession).where(
        RefreshSession.user_id == donor_id, RefreshSession.role == "donor",
    ))
    for table in (OtpCode, OtpFailureWindow):
        await session.execute(delete(table).where(
            table.purpose.in_([PURPOSE_DONOR_RESET, PURPOSE_DONOR_ENROLLMENT]), func.lower(table.email) == email,
        ))
    await session.execute(delete(AuthenticationDetailsDonor).where(
        AuthenticationDetailsDonor.auth_id == donor.authentication_id,
    ))
    await session.execute(delete(QueryTable).where(QueryTable.donor_id == donor_id))

    responses = await session.scalars(select(ResponseDetails).where(
        ResponseDetails.donor_ids.contains(donor_id, autoescape=True),
    ).order_by(ResponseDetails.id).with_for_update())
    for response in responses:
        ids = [value.strip() for value in response.donor_ids.split(",") if value.strip()]
        if donor_id in ids:
            response.donor_ids = ",".join(value for value in ids if value != donor_id) or None
            # The report is unstructured and may contain details about a participating donor.
            response.report = None

    certificates = (await session.scalars(select(AdminAuditLog).where(
        AdminAuditLog.entity_type == "certificate", AdminAuditLog.detail == f"donor_id={donor_id}",
    ))).all()
    # Sending an existing certificate to an address does not establish that the
    # recipient is the donor identified on the certificate.
    filenames = {entry.entity_id for entry in certificates
                 if entry.action == "certificate.generate" and entry.entity_id}
    for filename in sorted(filenames):
        if await session.get(ErasureFile, filename) is None:
            session.add(ErasureFile(filename=filename))
    for entry in certificates:
        entry.entity_id = entry.detail = None
    if filenames:
        await session.execute(update(AdminAuditLog).where(
            AdminAuditLog.entity_type == "certificate", AdminAuditLog.entity_id.in_(filenames),
        ).values(entity_id=None, detail=None))
    await session.execute(update(AdminAuditLog).where(
        AdminAuditLog.entity_type == "donor", AdminAuditLog.entity_id == donor_id,
    ).values(entity_id=None, detail=None))

    await session.execute(delete(DonorDetail).where(DonorDetail.id == donor_id))
    for model, relation, identifier in (
        (PersonalDetails, DonorDetail.personal_details_id, donor.personal_details_id),
        (AddressDetails, DonorDetail.address_id, donor.address_id),
        (DiseaseDetails, DonorDetail.disease_id, donor.disease_id),
    ):
        # Legacy rows may share a parent. Keep it while any other donor references it.
        others = select(DonorDetail.id).where(relation == identifier).exists()
        await session.execute(delete(model).where(model.id == identifier, ~others))
