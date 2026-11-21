"""Cross-role authorization matrix, generated from the OpenAPI spec (P3-52).

Every operation is either on an explicit PUBLIC allowlist or requires a bearer token, so a new
unauthenticated route fails this test until someone reviews it. Secured operations are then
exercised with: no token, a garbage token, a refresh token, an inactive account, a donor token
and an admin token.
"""

import re
from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.api.auth.utils import create_access_token, create_refresh_token
from app.main import app
from tests.helpers import insert_donor

# (method, path) of operations that are intentionally reachable without a token.
PUBLIC = {
    ("GET", "/api/v1/"),
    ("GET", "/api/v1/health"),
    ("POST", "/api/v1/admins/register"),  # gated by an invite OTP instead
    ("POST", "/api/v1/auth/admin/login"),
    ("POST", "/api/v1/auth/admin/password-reset/confirm"),
    ("POST", "/api/v1/auth/admin/password-reset/request"),
    ("POST", "/api/v1/auth/donor/login"),
    ("POST", "/api/v1/auth/donor/password-reset/confirm"),
    ("POST", "/api/v1/auth/donor/password-reset/request"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/blood-requests/"),
    ("POST", "/api/v1/donors/register"),
    ("GET", "/api/v1/hospitals/"),
    ("GET", "/api/v1/hospitals/autofill"),
    ("GET", "/api/v1/hospitals/blood-banks"),
    ("GET", "/api/v1/hospitals/cities"),
    ("GET", "/api/v1/hospitals/{hospital_id}"),
    ("POST", "/api/v1/queries/"),
}
# Secured operations a donor may call (everything else secured is admin-only).
DONOR_ALLOWED = {
    ("PATCH", "/api/v1/donors/{donor_id}"),  # own profile only, see test_donor_cannot_edit_another_donor
    ("GET", "/api/v1/queries/my-queries"),
    ("POST", "/api/v1/privacy/erasure-requests"),
    ("GET", "/api/v1/privacy/erasure-requests/mine"),
    ("POST", "/api/v1/auth/logout-all"),  # every account may revoke its own sessions
}
# Secured operations that need a donor token: admins are refused.
DONOR_ONLY = {
    ("PATCH", "/api/v1/donors/{donor_id}"),
    ("POST", "/api/v1/privacy/erasure-requests"),
    ("GET", "/api/v1/privacy/erasure-requests/mine"),
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _operations():
    spec = app.openapi()
    for path, ops in sorted(spec["paths"].items()):
        for method, op in ops.items():
            if method in HTTP_METHODS:
                yield method.upper(), path, bool(op.get("security"))


OPS = list(_operations())
SECURED = [(m, p) for m, p, sec in OPS if sec]


def _url(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "X-1", path)


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def donor_token(sub="DON-1", email="donor1@example.com") -> str:
    return create_access_token({"sub": sub, "user_type": "donor", "email": email})


def test_every_unprotected_operation_is_on_the_public_allowlist():
    unprotected = {(m, p) for m, p, sec in OPS if not sec}
    assert unprotected == PUBLIC


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", SECURED)
async def test_secured_operation_token_matrix(client: AsyncClient, test_session, method, path):
    """One fixture setup per operation: the matrix is cheap to extend but slow to set up."""
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2, active=False)
    url = _url(path)
    donor = {"sub": "DON-1", "user_type": "donor", "email": "donor1@example.com"}

    async def status_for(headers=None):
        return (await client.request(method, url, headers=headers)).status_code

    assert await status_for() == 401, "no token"
    assert await status_for(_bearer("garbage")) == 401, "garbage token"
    expired = create_access_token(donor, expires_delta=timedelta(seconds=-5))
    assert await status_for(_bearer(expired)) == 401, "expired token"
    assert await status_for(_bearer(create_refresh_token(donor))) == 401, "refresh token used as access token"
    inactive = donor_token("DON-2", "donor2@example.com")
    assert await status_for(_bearer(inactive)) == 401, "inactive donor"
    if (method, path) not in DONOR_ALLOWED:
        assert await status_for(_bearer(donor_token())) == 403, "donor on an admin-only operation"


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", sorted(DONOR_ONLY))
async def test_admin_token_is_forbidden_on_donor_only_operations(admin_client: AsyncClient, method, path):
    r = await admin_client.request(method, _url(path), json={"name": "Someone"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_donor_cannot_edit_another_donor(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    r = await client.patch("/api/v1/donors/DON-2", json={"name": "Hijacked"}, headers=_bearer(donor_token()))
    assert r.status_code == 403
    own = await client.patch("/api/v1/donors/DON-1", json={"name": "Renamed Donor"}, headers=_bearer(donor_token()))
    assert own.status_code == 200


@pytest.mark.asyncio
async def test_my_queries_only_returns_the_callers_queries(client: AsyncClient, test_session):
    await insert_donor(test_session, 1)
    await insert_donor(test_session, 2)
    # Each donor files a query while signed in; ownership follows the account (see test_query_ownership).
    for n, who in ((1, "donor1"), (2, "donor2")):
        r = await client.post(
            "/api/v1/queries/",
            json={"user_name": who, "user_email": f"{who}@example.com", "user_query": f"Question from {who} please"},
            headers=_bearer(donor_token(f"DON-{n}", f"{who}@example.com")),
        )
        assert r.status_code == 201
    # An anonymous query that mentions donor1's address must not show up for donor1.
    await client.post("/api/v1/queries/", json={
        "user_name": "anon", "user_email": "donor1@example.com", "user_query": "Anonymous note naming donor1",
    })
    mine = await client.get("/api/v1/queries/my-queries", headers=_bearer(donor_token()))
    assert mine.status_code == 200
    assert {q["user_query"] for q in mine.json()} == {"Question from donor1 please"}
