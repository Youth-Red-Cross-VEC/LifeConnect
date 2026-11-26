"""Transaction invariants exercised with independent PostgreSQL connections."""
import asyncio
from datetime import datetime
import os
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from app.core.request_status import BloodRequestStatus
from app.models.base import Base
from app.models.donor import DonorDetail
from app.models.otp import OtpCode
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.services.otp_service import store_otp, verify_otp
from tests.helpers import insert_donor, insert_request


@pytest.fixture
async def sessions():
    url = os.getenv("LC_AUTH_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("requires disposable PostgreSQL")
    schema = "txn_test_" + uuid4().hex
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.execute(CreateSchema(schema))
            await conn.run_sync(Base.metadata.create_all)
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        async with engine.begin() as conn:
            await conn.execute(DropSchema(schema, cascade=True, if_exists=True))
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_first_issue_and_rollback_of_consumption(sessions):
    email = "txn@example.test"
    async def issue(code):
        async with sessions() as session:
            await store_otp(session, email, code, "invite")
    await asyncio.gather(issue("123456"), issue("654321"))
    async with sessions() as session:
        row = (await session.scalars(select(OtpCode))).one()
        assert row.attempts == 0
        await store_otp(session, email, "345678", "invite")
        assert await verify_otp(session, email, "345678", "invite", commit_success=False)
        await session.rollback()
    async def consume():
        async with sessions() as session:
            return await verify_otp(session, email, "345678", "invite")
    assert sorted(await asyncio.gather(consume(), consume())) == [False, True]


@pytest.mark.asyncio
async def test_competing_close_and_failure_preserve_donation(sessions):
    async with sessions() as session:
        await insert_donor(session)
        await insert_request(session)
        await DonorRepository(session).update_last_donated("DON-1", datetime(2026, 3, 1))
        await session.commit()

    async def close(rollback=False):
        async with sessions() as session:
            changed = await BloodRequestRepository(session).update_status(
                "REQ-1", BloodRequestStatus.CLOSED, expected_status="Approved",
            )
            if changed:
                await DonorRepository(session).update_last_donated("DON-1", datetime(2026, 2, 1))
            if rollback:
                await session.rollback()
            else:
                await session.commit()
            return changed

    assert await close(rollback=True)
    assert sorted(await asyncio.gather(close(), close())) == [False, True]
    async with sessions() as session:
        donor = await session.get(DonorDetail, "DON-1")
        assert donor.number_of_times_donated == 2
        assert donor.last_donated_date == datetime(2026, 3, 1)

@pytest.mark.asyncio
async def test_failed_approval_rolls_back_and_competing_decisions_have_one_winner(sessions):
    from sqlalchemy.exc import IntegrityError
    from app.models.blood_request import ResponseDetails

    async with sessions() as session:
        await insert_request(session, status="Pending")
        repo = BloodRequestRepository(session)
        assert await repo.update_status("REQ-1", BloodRequestStatus.APPROVED, expected_status="Pending")
        session.add(ResponseDetails(id="RESP-1"))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    async def decide(target):
        async with sessions.begin() as session:
            return await BloodRequestRepository(session).update_status(
                "REQ-1", target, expected_status="Pending",
            )
    assert sorted(await asyncio.gather(
        decide(BloodRequestStatus.APPROVED), decide(BloodRequestStatus.DECLINED),
    )) == [False, True]

@pytest.mark.asyncio
async def test_parallel_hospital_inserts_have_one_winner(sessions):
    from sqlalchemy.exc import IntegrityError
    from app.models.hospital import HospitalDetails

    async def create(name, branch):
        try:
            async with sessions.begin() as session:
                session.add(HospitalDetails(
                    id=str(uuid4()), hospital_name=name, branch=branch, pincode="600001",
                    hospital_address="Synthetic", city="Test", state="Test", country="Test",
                ))
        except IntegrityError:
            return False
        return True

    assert sorted(await asyncio.gather(create("Clinic", None), create("CLINIC", ""))) == [False, True]

@pytest.mark.parametrize("kind", ["sqlite", "postgres"])
def test_hospital_index_refuses_legacy_duplicates_without_data_loss(tmp_path, kind):
    from tests.test_migrations import _database_urls, _run_alembic
    from tests.test_email_migration import _run
    from tests.test_upgrade_from_0004 import _fetch

    urls = dict(_database_urls(tmp_path))
    if kind not in urls:
        pytest.skip("requires disposable PostgreSQL")
    url = urls[kind]
    def migrate(*args):
        result = _run_alembic(url, *args)
        assert result.returncode == 0, result.stderr

    migrate("upgrade", "head")
    migrate("downgrade", "0013")
    seed = "INSERT INTO hospital_details (id,hospital_name,branch,pincode,hospital_address,city,state,country,created_at) "
    scope = " WHERE id IN ('txn-h1','txn-h2')"
    try:
        asyncio.run(_run(url, [
            seed + "VALUES ('txn-h1','Clinic',NULL,'600001','Test','Test','Test','Test','2026-01-01')",
            seed + "VALUES ('txn-h2','CLINIC','','600001','Test','Test','Test','Test','2026-01-01')",
        ]))
        result = _run_alembic(url, "upgrade", "0014")
        assert result.returncode and "Duplicate hospital identity" in result.stderr
        assert asyncio.run(_fetch(url, "SELECT version_num FROM alembic_version")) == [("0013",)]
        assert asyncio.run(_fetch(url, "SELECT count(*) FROM hospital_details" + scope)) == [(2,)]
    finally:
        asyncio.run(_run(url, ["DELETE FROM hospital_details" + scope]))
        migrate("upgrade", "head")
