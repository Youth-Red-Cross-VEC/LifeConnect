"""Authorization regression tests for endpoints hardened in the security audit."""

import pytest
from httpx import AsyncClient

from datetime import datetime, timedelta

from sqlalchemy import select

from app.models.otp import OtpCode
from app.services.otp_service import (
    PURPOSE_ADMIN_INVITE,
    PURPOSE_ADMIN_RESET,
    PURPOSE_DONOR_RESET,
    generate_otp,
    store_otp,
    verify_otp,
)
from app.services.certificate_service import CertificateService


class TestUnauthenticatedAccess:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/api/v1/queries/1"),
            ("get", "/api/v1/queries/my-queries"),
            ("get", "/api/v1/certificates/download/x_20240101_000000_certificate.png"),
            ("post", "/api/v1/certificates/send-email?filename=a&donor_id=b"),
            ("get", "/api/v1/blood-requests/REQ-1"),
        ],
    )
    async def test_requires_auth(self, client: AsyncClient, method, path):
        response = await getattr(client, method)(path)
        assert response.status_code == 401


class TestOtp:
    def test_otp_is_six_digits(self):
        for _ in range(50):
            assert len(generate_otp()) == 6

    @pytest.mark.asyncio
    async def test_otp_is_single_use_and_purpose_bound(self, test_session):
        await store_otp(test_session, "a@example.com", "123456", PURPOSE_DONOR_RESET)
        assert not await verify_otp(test_session, "a@example.com", "123456", PURPOSE_ADMIN_RESET)
        assert not await verify_otp(test_session, "a@example.com", "123456", PURPOSE_ADMIN_INVITE)
        assert await verify_otp(test_session, "a@example.com", "123456", PURPOSE_DONOR_RESET)
        assert not await verify_otp(test_session, "a@example.com", "123456", PURPOSE_DONOR_RESET)

    @pytest.mark.asyncio
    async def test_otp_attempt_limit(self, test_session):
        await store_otp(test_session, "b@example.com", "123456", PURPOSE_DONOR_RESET)
        for _ in range(5):
            assert not await verify_otp(test_session, "b@example.com", "000000", PURPOSE_DONOR_RESET)
        assert not await verify_otp(test_session, "b@example.com", "123456", PURPOSE_DONOR_RESET)

    @pytest.mark.asyncio
    async def test_otp_is_stored_hashed_and_expires(self, test_session):
        await store_otp(test_session, "c@example.com", "654321", PURPOSE_ADMIN_INVITE)
        row = (await test_session.execute(select(OtpCode))).scalar_one()
        assert "654321" not in row.otp_hash
        row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        await test_session.commit()
        assert not await verify_otp(test_session, "c@example.com", "654321", PURPOSE_ADMIN_INVITE)

    @pytest.mark.asyncio
    async def test_new_code_replaces_old_one(self, test_session):
        await store_otp(test_session, "d@example.com", "111111", PURPOSE_ADMIN_INVITE)
        await store_otp(test_session, "d@example.com", "222222", PURPOSE_ADMIN_INVITE)
        assert not await verify_otp(test_session, "d@example.com", "111111", PURPOSE_ADMIN_INVITE)

    def test_no_weak_rng_or_process_local_store(self):
        import inspect
        import app.api.v1.admins as admins
        import app.api.auth.router as auth_router
        assert "random.randint" not in inspect.getsource(admins)
        assert not hasattr(auth_router, "otp_store")


class TestCertificatePaths:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", ["../secret.png", "..\secret.png", "a/b.png", "x.png", ""])
    async def test_rejects_bad_filenames(self, tmp_path, name):
        svc = CertificateService(output_dir=str(tmp_path))
        assert await svc.get_certificate(name) is None
        assert await svc.delete_certificate(name) is False
