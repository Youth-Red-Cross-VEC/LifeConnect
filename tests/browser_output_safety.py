"""Verify stored user text at the React DOM boundary using only inert markup."""
import os

from tests.browser_donor_reset import ORIGIN, browser_route
from tests.helpers import insert_admin


async def test_query_is_text_in_admin_browser(client, test_session):
    from playwright.async_api import async_playwright, expect

    name = "Élodie O’Connor"
    message = 'About <strong data-lc-marker="yes">blood groups</strong> & eligibility'
    saved = await client.post("/api/v1/queries/", json={
        "user_email": "visitor@example.com", "user_name": name, "user_query": message,
    })
    assert saved.status_code == 201
    await insert_admin(test_session, 1)
    login = await client.post("/api/v1/auth/admin/login", json={"email": "admin1@example.com", "password": "Secret123"})
    assert login.status_code == 200

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=os.getenv("LIFECONNECT_TEST_CHROMIUM"))
        try:
            page = await browser.new_page()
            await page.route("**/*", browser_route(client, "/api/v1/queries/", []))
            await page.goto(f"{ORIGIN}/admin/queries")
            await expect(page.get_by_role("cell", name=name, exact=True)).to_be_visible()
            cell = page.get_by_role("cell", name=message, exact=True)
            await expect(cell).to_be_visible()
            assert await cell.inner_text() == message
            assert await page.locator("[data-lc-marker]").count() == 0
        finally:
            await browser.close()
