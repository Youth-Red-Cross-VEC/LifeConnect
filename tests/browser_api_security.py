"""Donor submits a blood request through the bounded hospital search and strict JSON API."""
import os
from datetime import date, timedelta

from sqlalchemy import select

from app.models.blood_request import BloodRequestDetails
from tests.browser_donor_reset import ORIGIN, browser_route
from tests.helpers import insert_donor, insert_request


async def test_blood_request_in_browser(client, test_session):
    from playwright.async_api import async_playwright

    await insert_request(test_session, 1)
    await insert_donor(test_session, 1)
    login = await client.post("/api/v1/auth/donor/login", json={"email": "donor1@example.com", "password": "Secret123"})
    assert login.status_code == 200
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=os.getenv("LIFECONNECT_TEST_CHROMIUM"))
        try:
            page = await browser.new_page()
            await page.route("**/*", browser_route(client, "/api/v1/blood-requests/", []))
            await page.goto(f"{ORIGIN}/donor/generate-request")
            for field, value in {
                "patient_name": "Browser Test", "attendant_name": "Contact", "patient_age": "28",
                "contact_number": "9000000000", "units_required": "1", "request_reason": "Test request",
                "due_date": (date.today() + timedelta(days=3)).isoformat(), "hospital_name": "Example",
            }.items():
                await page.locator(f"#{field}").fill(value)
            await page.get_by_text("Example General Hospital", exact=True).click()
            await page.locator("#blood_group").select_option("O+")
            await page.get_by_role("button", name="Submit Request").click()
            await page.wait_for_url("**/blood-request/confirmation")
            row = await test_session.scalar(select(BloodRequestDetails).where(BloodRequestDetails.patient_name == "Browser Test"))
            assert row.hospital_id == "HOSP-1" and row.status == "Pending"
        finally:
            await browser.close()
