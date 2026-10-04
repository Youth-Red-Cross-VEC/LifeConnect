"""Authorization regression tests for endpoints hardened in the security audit."""

import pytest
from httpx import AsyncClient

from app.api.auth.router import generate_otp, store_otp, verify_otp
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

    def test_otp_is_single_use_and_purpose_bound(self):
        store_otp("a@example.com", "123456", "donor_password_reset")
        assert not verify_otp("a@example.com", "123456", "admin_password_reset")
        assert verify_otp("a@example.com", "123456", "donor_password_reset")
        assert not verify_otp("a@example.com", "123456", "donor_password_reset")

    def test_otp_attempt_limit(self):
        store_otp("b@example.com", "123456", "donor_password_reset")
        for _ in range(5):
            assert not verify_otp("b@example.com", "000000", "donor_password_reset")
        assert not verify_otp("b@example.com", "123456", "donor_password_reset")


class TestCertificatePaths:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", ["../secret.png", "..\secret.png", "a/b.png", "x.png", ""])
    async def test_rejects_bad_filenames(self, tmp_path, name):
        svc = CertificateService(output_dir=str(tmp_path))
        assert await svc.get_certificate(name) is None
        assert await svc.delete_certificate(name) is False
