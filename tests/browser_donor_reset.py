"""Opt-in Chromium test of the built React app against FastAPI with synthetic mail."""

import mimetypes
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from sqlalchemy import update

from app.models.otp import OtpCode
from app.utils.dates import utcnow
from tests.helpers import insert_admin, insert_donor
from tests.test_donor_password_reset import auth_router

DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
ORIGIN = "http://lifeconnect.test"


@pytest.mark.parametrize(
    "role,email,make_account,otp_stage,new_password_label,confirm_password_label",
    [
        ("donor", "donor1@example.com", insert_donor, "otp-validation", "New Password", "Confirm Password"),
        ("admin", "admin1@example.com", insert_admin, "otp-verification",
         "Enter Your New Password", "Confirm Your New Password"),
    ],
)
async def test_password_reset_in_browser(
    client, test_session, monkeypatch, role, email, make_account, otp_stage,
    new_password_label, confirm_password_label,
):
    from playwright.async_api import async_playwright, expect

    await make_account(test_session, 1)
    reset = f"/api/v1/auth/{role}/password-reset"
    sent = []

    async def capture_code(email, otp, name):
        sent.append(otp)

    monkeypatch.setattr(auth_router, "_send_reset_email", capture_code)
    assert (DIST / "index.html").is_file(), "Run npm run build in frontend first"
    posts = []

    async def serve(route):
        request = route.request
        path = urlsplit(request.url).path
        if path.startswith("/api/"):
            headers = {
                "access-control-allow-origin": ORIGIN,
                "access-control-allow-credentials": "true",
                "access-control-allow-methods": "POST, OPTIONS",
                "access-control-allow-headers": "content-type",
            }
            if request.method == "OPTIONS":
                await route.fulfill(status=204, headers=headers)
                return
            if path.startswith(reset):
                posts.append(path)
            response = await client.request(request.method, path, content=request.post_data,
                                            headers={"content-type": "application/json"})
            await route.fulfill(status=response.status_code, headers=headers,
                                body=response.content, content_type="application/json")
        elif request.url.startswith(f"{ORIGIN}/"):
            asset = (DIST / path.lstrip("/")).resolve()
            if not asset.is_relative_to(DIST) or not asset.is_file():
                asset = DIST / "index.html"
            await route.fulfill(path=asset, content_type=mimetypes.guess_type(asset)[0])
        else:
            await route.abort()

    async with async_playwright() as playwright:
        chromium = await playwright.chromium.launch(executable_path=os.getenv("LIFECONNECT_TEST_CHROMIUM"))
        page = await chromium.new_page()
        await page.route("**/*", serve)
        try:
            for stage in (otp_stage, "new-password"):
                await page.goto(f"{ORIGIN}/{role}/{stage}")
                await expect(page.get_by_role("heading", name="Forgot Password")).to_be_visible()

            async def request_code():
                await page.get_by_label("Email Address").fill(email)
                await page.get_by_role("button", name="Send OTP").click()
                await expect(page.get_by_label("Enter OTP")).to_be_visible()

            await request_code()
            await page.reload()
            await expect(page.get_by_role("heading", name="Forgot Password")).to_be_visible()
            await request_code()

            await page.get_by_label("Enter OTP").fill("123")
            await page.get_by_role("button", name="Continue").click()
            await expect(page.get_by_role("alert")).to_contain_text("six-digit")

            async def enter_code():
                await page.get_by_label("Enter OTP").fill(sent[-1])
                await page.get_by_role("button", name="Continue").click()
                await expect(page.get_by_label("Email", exact=True)).to_have_value(email)

            await enter_code()
            assert posts == [f"{reset}/request"] * 2
            assert await page.evaluate("history.state.usr == null")

            await page.get_by_label(new_password_label, exact=True).fill("Replacement123")
            await page.get_by_label(confirm_password_label, exact=True).fill("Different123")
            await page.get_by_role("button", name="Reset Password").click()
            await expect(page.get_by_role("alert")).to_have_text("Passwords do not match")
            assert posts == [f"{reset}/request"] * 2

            await test_session.execute(update(OtpCode).values(expires_at=utcnow() - timedelta(seconds=1)))
            await test_session.commit()
            await page.get_by_label(confirm_password_label, exact=True).fill("Replacement123")
            await page.get_by_role("button", name="Reset Password").click()
            await expect(page.get_by_role("alert")).to_have_text("Invalid or expired code")
            await page.get_by_role("link", name="Request a new code").click()
            await request_code()
            await enter_code()
            await page.get_by_label(new_password_label, exact=True).fill("Replacement123")
            await page.get_by_label(confirm_password_label, exact=True).fill("Replacement123")
            await page.get_by_role("button", name="Reset Password").click()
            await expect(page).to_have_url(f"{ORIGIN}/{role}/login")
            await expect(page.get_by_role("status")).to_contain_text("Password reset successful")
        finally:
            await chromium.close()
