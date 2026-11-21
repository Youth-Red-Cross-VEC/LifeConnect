"""Opt-in browser check for the donor-to-reviewer erasure journey."""

import mimetypes
import os
from urllib.parse import urlsplit

from app.core.request_status import AdminRole
from tests.browser_donor_reset import DIST, ORIGIN
from tests.helpers import insert_admin, insert_donor
from tests.test_erasure import URL, login


async def test_erasure_in_browser(client, test_session):
    from playwright.async_api import async_playwright, expect

    await insert_donor(test_session)
    await insert_admin(test_session, 1, role=AdminRole.SUPER_ADMIN)
    donor_headers, donor_cookie = await login(client, "donor", "donor1@example.com")
    _, admin_cookie = await login(client, "admin", "admin1@example.com")
    assert (DIST / "index.html").is_file(), "Run npm run build in frontend first"

    def handle(cookie):
        async def serve(route):
            request = route.request
            path = urlsplit(request.url).path
            if path.startswith("/api/"):
                cors = {
                    "access-control-allow-origin": ORIGIN,
                    "access-control-allow-credentials": "true",
                    "access-control-allow-methods": "GET, POST, PATCH, OPTIONS",
                    "access-control-allow-headers": "content-type, authorization",
                }
                if request.method == "OPTIONS":
                    await route.fulfill(status=204, headers=cors)
                    return
                headers = {"content-type": "application/json", "cookie": f"lc_refresh_token={cookie}"}
                if "authorization" in request.headers:
                    headers["authorization"] = request.headers["authorization"]
                response = await client.request(
                    request.method, path, content=request.post_data, headers=headers,
                )
                await route.fulfill(status=response.status_code, headers=cors,
                                    body=response.content, content_type="application/json")
            elif request.url.startswith(f"{ORIGIN}/"):
                asset = (DIST / path.lstrip("/")).resolve()
                if not asset.is_relative_to(DIST) or not asset.is_file():
                    asset = DIST / "index.html"
                await route.fulfill(path=asset, content_type=mimetypes.guess_type(asset)[0])
            else:
                await route.abort()

        return serve

    async with async_playwright() as playwright:
        chromium = await playwright.chromium.launch(executable_path=os.getenv("LIFECONNECT_TEST_CHROMIUM"))
        donor_page = await chromium.new_page()
        admin_page = await chromium.new_page()
        await donor_page.route("**/*", handle(donor_cookie))
        await admin_page.route("**/*", handle(admin_cookie))
        try:
            await donor_page.goto(f"{ORIGIN}/donor/privacy")
            await donor_page.get_by_label("Current password").fill("Secret123")
            await donor_page.get_by_role("button", name="Request erasure").click()
            await expect(donor_page.get_by_text("Awaiting review.", exact=False)).to_be_visible()

            await admin_page.goto(f"{ORIGIN}/admin/privacy")
            await expect(admin_page.get_by_text("Donor DON-1", exact=False)).to_be_visible()
            await admin_page.get_by_role("button", name="Approve", exact=True).click()
            await expect(admin_page.get_by_text("Permanently erase this account?")).to_be_visible()
            await admin_page.get_by_role("button", name="Confirm", exact=True).click()
            await expect(admin_page.get_by_text("Account erasure approved.")).to_be_visible()
            await expect(admin_page.get_by_text("There are no pending requests.")).to_be_visible()
            assert (await client.get(f"{URL}/mine", headers=donor_headers)).status_code == 401
        finally:
            await chromium.close()
