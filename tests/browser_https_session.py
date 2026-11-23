"""Opt-in HTTPS Edge journey with real Nginx, Uvicorn and disposable SQLite accounts."""
import asyncio
import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest
import uvicorn
from playwright.async_api import async_playwright

from app.config import get_settings
from app.main import app
from app.services.certificate_service import CertificateService, get_certificate_service
from tests.helpers import insert_admin


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def test_https_session_and_certificate(client, test_session, tmp_path, monkeypatch):
    nginx = os.getenv("LIFECONNECT_TEST_NGINX") or shutil.which("nginx")
    openssl = os.getenv("LIFECONNECT_TEST_OPENSSL") or shutil.which("openssl")
    if not nginx or not openssl:
        pytest.skip("Set LIFECONNECT_TEST_NGINX and LIFECONNECT_TEST_OPENSSL for the HTTPS proxy journey")

    from tests.helpers import insert_donor
    await insert_donor(test_session)
    await insert_admin(test_session)
    monkeypatch.setattr(get_settings(), "APP_ENV", "production")
    service = CertificateService(output_dir=str(tmp_path / "certificates"))
    monkeypatch.setitem(app.dependency_overrides, get_certificate_service, lambda: service)
    subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                    "-subj", "/CN=localhost", "-keyout", "key.pem", "-out", "cert.pem"],
                   cwd=tmp_path, check=True, capture_output=True)

    backend, first, second = port(), port(), port()
    (tmp_path / "logs").mkdir()
    (tmp_path / "temp").mkdir()
    site = (Path(__file__).resolve().parents[1] / "frontend/nginx-site.conf").read_text()
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    dist = (frontend / "dist").as_posix()
    site = site.replace("root /usr/share/nginx/html;", f'root "{dist}";')
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    shutil.copy(frontend / "security-headers.conf", snippets)
    log_format = (frontend / "nginx-upstream.conf").read_text().splitlines()[0]
    assert log_format.startswith("log_format lifeconnect_safe")
    config = f"""
daemon off;
master_process off;
events {{ worker_connections 64; }}
http {{
    {log_format}
    access_log logs/access.log lifeconnect_safe;
    types {{ text/html html; application/javascript js; text/css css; }}
    map $scheme $lifeconnect_hsts {{ https "max-age=31536000"; }}
    upstream lifeconnect_api {{ server 127.0.0.1:{backend}; }}
    server {{
        listen 127.0.0.1:{first} ssl;
        server_name localhost;
        ssl_certificate cert.pem;
        ssl_certificate_key key.pem;
        location = / {{ default_type text/html; return 200 '<html>LifeConnect test</html>'; }}
        {site}
    }}
    # A separate site controls its own CSP. Exercise the API origin check even
    # when the referring page allows the cross-origin request to be issued.
    server {{
        listen 127.0.0.1:{second} ssl;
        ssl_certificate cert.pem;
        ssl_certificate_key key.pem;
        location / {{ default_type text/html; return 200 '<html>Separate origin</html>'; }}
    }}
}}
"""
    (tmp_path / "nginx.conf").write_text(config, encoding="utf8")
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=backend, proxy_headers=True,
                                            forwarded_allow_ips="127.0.0.1", lifespan="off", access_log=False))
    serving = asyncio.create_task(server.serve())
    process = None
    try:
        process = await asyncio.create_subprocess_exec(nginx, "-p", tmp_path.as_posix() + "/", "-c", "nginx.conf",
                                                        cwd=tmp_path, stderr=asyncio.subprocess.PIPE)
        origin = f"https://localhost:{first}"
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path=os.getenv("LIFECONNECT_TEST_CHROMIUM"))
            try:
                context = await browser.new_context(ignore_https_errors=True)
                page = await context.new_page()
                await context.route("https://**/*", lambda route: route.continue_() if route.request.url.startswith("https://localhost:") else route.abort())
                spa = await page.goto(origin + "/donor/login?privacy_marker=synthetic")
                assert spa.status == 200 and "frame-ancestors 'none'" in spa.headers["content-security-policy"]
                await page.locator('input[type="password"]').wait_for()
                await page.goto(origin)
                async def post(path, body=None):
                    return await page.evaluate("""async ([url, body]) => {
                        const res = await fetch(url, {method: 'POST', headers: {'Content-Type':'application/json'},
                            body: body ? JSON.stringify(body) : undefined});
                        return [res.status, await res.json()];
                    }""", [path, body])

                login = "/api/v1/auth/admin/login"
                refresh = "/api/v1/auth/refresh"
                logout = "/api/v1/auth/logout"
                status, account = await post(login, {"email": "admin1@example.com", "password": "Secret123"})
                assert status == 200
                cookie, = await context.cookies()
                assert cookie["name"] == "__Host-lc_refresh_token" and cookie["path"] == "/"
                assert cookie["secure"] and cookie["httpOnly"] and cookie["sameSite"] == "Strict"
                assert not await page.evaluate("document.cookie")
                await page.goto(f"https://localhost:{second}")
                async with page.expect_response(lambda res: res.url == origin + logout) as intercepted:
                    await page.evaluate("""url => fetch(url, {method:'POST', credentials:'include', mode:'no-cors'})""",
                                        origin + logout)
                assert (await intercepted.value).status == 403
                await page.goto(origin)
                status, _ = await post(refresh)
                assert status == 200 and (await context.cookies())[0]["value"] != cookie["value"]

                headers = {"Authorization": "Bearer " + account["access_token"]}
                generated = await context.request.post(origin + "/api/v1/certificates/generate", headers=headers,
                    data={"donor_id": "DON-1", "donation_date": "2026-01-15", "send_email": False})
                assert generated.status == 201
                name = (await generated.json())["filename"]
                download = origin + "/api/v1/certificates/download/" + name
                assert (await context.request.get(download)).status == 401
                file = await context.request.get(download, headers=headers)
                assert file.status == 200 and (await file.body()).startswith(b"\x89PNG")
                assert file.headers["strict-transport-security"] == "max-age=31536000"
                assert "default-src 'none'" in file.headers["content-security-policy"]
                assert "privacy_marker" not in (tmp_path / "logs/access.log").read_text()
                assert "attachment" in file.headers["content-disposition"]
                status, donor = await post("/api/v1/auth/donor/login",
                                          {"email": "donor1@example.com", "password": "Secret123"})
                assert status == 200
                replaced, = await context.cookies()
                assert replaced["value"] != cookie["value"]
                denied = await context.request.get(download, headers={"Authorization": "Bearer " + donor["access_token"]})
                assert denied.status == 403
                assert (await post(logout))[0] == 200 and not await context.cookies()
                assert (await post(refresh))[0] == 401
            finally:
                await browser.close()
    finally:
        if process and process.returncode is None:
            process.terminate()
            await process.wait()
        server.should_exit = True
        await serving
