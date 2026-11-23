"""Session writes are origin checked independently of CORS response visibility."""
import pytest

from tests.helpers import insert_donor

LOGIN = "/api/v1/auth/donor/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"


@pytest.mark.parametrize("origin", ["https://other.example.test", "null", "http://test.evil.invalid"])
async def test_rejected_origin_cannot_replace_rotate_or_revoke_session(client, test_session, origin):
    await insert_donor(test_session)
    body = {"email": "donor1@example.com", "password": "Secret123"}
    assert (await client.post(LOGIN, json=body, headers={"Origin": "http://test"})).status_code == 200
    for path in (LOGIN, REFRESH, LOGOUT):
        response = await client.post(path, headers={"Origin": origin}, json=body if path == LOGIN else None)
        assert response.status_code == 403 and "set-cookie" not in response.headers
    assert (await client.post(REFRESH, headers={"Origin": "http://test"})).status_code == 200


async def test_originless_cookie_requests_need_non_simple_content_type(client, test_session):
    await insert_donor(test_session)
    body = {"email": "donor1@example.com", "password": "Secret123"}
    await client.post(LOGIN, json=body)
    for headers in ({}, {"Content-Type": "text/plain"}, [("origin", "http://test"), ("origin", "http://test")]):
        assert (await client.post(LOGOUT, headers=headers)).status_code == 403
    assert (await client.post(REFRESH, headers={"Content-Type": "application/json"})).status_code == 200
    assert (await client.post(LOGOUT, headers={"Content-Type": "application/json"})).status_code == 200
    assert (await client.post(REFRESH, headers={"Content-Type": "application/json"})).status_code == 401


async def test_credentialed_cors_preflight(client):
    origin = "http://localhost:5173"
    headers = {"Origin": origin, "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "authorization,content-type"}
    good = await client.options(REFRESH, headers=headers)
    assert good.status_code == 200
    assert good.headers["access-control-allow-origin"] == origin
    assert good.headers["access-control-allow-credentials"] == "true"
    assert "Origin" in good.headers["vary"]
    for change in ({"Origin": "https://other.example.test"}, {"Access-Control-Request-Method": "TRACE"},
                   {"Access-Control-Request-Headers": "x-unapproved"}):
        assert (await client.options(REFRESH, headers={**headers, **change})).status_code == 400


async def test_missing_cookie_responses_do_not_modify_cookie_jar(client):
    for path, expected in ((REFRESH, 401), (LOGOUT, 200)):
        response = await client.post(path)
        assert response.status_code == expected
        assert "set-cookie" not in response.headers


async def test_https_does_not_adopt_a_legacy_cookie(client, test_session, monkeypatch):
    from http.cookies import SimpleCookie
    from app.config import get_settings
    await insert_donor(test_session)
    monkeypatch.setattr(get_settings(), "APP_ENV", "production")
    login = await client.post(LOGIN, json={"email": "donor1@example.com", "password": "Secret123"})
    assert login.status_code == 200
    token = SimpleCookie(login.headers["set-cookie"])["__Host-lc_refresh_token"].value
    rejected = await client.post(REFRESH, headers={"Cookie": "lc_refresh_token=" + token, "Origin": "http://test"})
    assert rejected.status_code == 401 and "set-cookie" not in rejected.headers
    accepted = await client.post(REFRESH, headers={"Cookie": "__Host-lc_refresh_token=" + token, "Origin": "http://test"})
    assert accepted.status_code == 200
