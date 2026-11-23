"""Built enrollment page and FastAPI with a synthetic mailbox."""
import os
from app.services.email_service import EmailService
from tests.browser_donor_reset import browser_route, ORIGIN


async def test_verified_enrollment_in_browser(client, monkeypatch):
    from playwright.async_api import async_playwright, expect

    sent = []
    async def capture(self, email, otp, name, purpose):
        sent.append(otp)
        return True

    monkeypatch.setattr(EmailService, "send_otp_email", capture)
    posts = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=os.getenv("LIFECONNECT_TEST_CHROMIUM"))
        try:
            page = await browser.new_page()
            await page.route("**/*", browser_route(client, "/api/v1/donors/register", posts))
            await page.goto(f"{ORIGIN}/donor/register")
            for field, value in {
                "Email": "new@example.com", "password": "NewPassword123", "confirm_password": "NewPassword123",
                "first_name": "Test", "age": "26", "dob": "2000-01-05", "contact_number": "9000000000",
                "address": "Test Street", "city": "Chennai", "pincode": "600001",
            }.items():
                await page.locator(f'input[name="{field}"]').fill(value)
            await page.locator('label[for="blood_group_O+"]').click()
            await page.locator('input[name="agree_terms"]').check()
            await page.get_by_role("button", name="Send verification code").click()
            verification = page.get_by_label("Six-digit code", exact=False)
            await expect(verification).to_be_visible()
            await verification.fill("000000")
            await page.get_by_role("button", name="Complete registration").click()
            await expect(page.get_by_text("Invalid or expired registration code")).to_be_visible()
            await verification.fill(sent[-1])
            await page.get_by_role("button", name="Complete registration").click()
            await page.wait_for_url("**/donor/registration-confirmation")
            assert posts == ["/api/v1/donors/register/code", "/api/v1/donors/register", "/api/v1/donors/register"]
        finally:
            await browser.close()
