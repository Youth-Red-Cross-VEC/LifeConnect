"""API transport, query, identifier and validation boundaries."""
import pytest
from app.core.api_limits import MAX_BODY_BYTES


async def test_streamed_and_declared_body_limits(client):
    async def chunks():
        yield b" " * MAX_BODY_BYTES
        yield b"x"

    url = "/api/v1/queries/"
    for content in (b"x" * (MAX_BODY_BYTES + 1), chunks()):
        response = await client.post(url, content=content, headers={"content-type": "application/json"})
        assert response.status_code == 413


@pytest.mark.parametrize(("body", "mime", "status"), [
    (b'{"user_name":"private","user_name":"other"}', "application/json", 400),
    (br'{"user_name":"abc\u0000def"}', "application/json", 400),
    (b"{", "application/json", 400), (b"{}", "text/plain", 415),
    (b'{"user_query":"private"}', "application/json", 422),
])
async def test_invalid_body_does_not_echo_input(client, body, mime, status):
    response = await client.post("/api/v1/queries/", content=body, headers={"content-type": mime})
    assert response.status_code == status
    assert "private" not in response.text


async def test_reject_ambiguous_headers_and_query(client):
    url = "/api/v1/hospitals/autofill"
    for query in ("q=xx&limit=-1", "q=xx&q=yy", "q=xx&typo=1", "q=%00xx"):
        assert (await client.get(f"{url}?{query}")).status_code == 422
    assert (await client.get(url, headers=[("Authorization", "a"), ("Authorization", "b")])).status_code == 400
    assert (await client.get(url, headers={"X-Test": "x" * 33000})).status_code == 431
    assert (await client.get(url, params={"q": "a"*4100})).status_code == 414


async def test_path_and_pagination_validation(admin_client):
    for path in ("/donors/" + "x"*37, "/queries/2147483648", "/blood-requests/pending?page=100001",
                 "/queries/?status=unknown", "/donors/blood-group/invalid", "/certificates/?limit=501"):
        assert (await admin_client.get("/api/v1" + path)).status_code == 422

async def test_default_limit_on_real_nested_routes_is_keyed_by_endpoint(client, monkeypatch):
    from app.core.rate_limiter import build_limiter
    from app.main import app

    monkeypatch.setattr(app.state, "limiter", build_limiter(2, "memory://"))
    paths = ["/api/v1/hospitals/H-1", "/api/v1/hospitals/H-2", "/api/v1/hospitals/H-3"]
    assert [(await client.get(path)).status_code for path in paths] == [404, 404, 429]
    assert (await client.get("/api/v1/hospitals/")).status_code == 200


async def test_body_rejected_on_bodyless_operation(client):
    response = await client.request("GET", "/api/v1/hospitals/", json={"unused": "value"})
    assert response.status_code == 422


async def test_city_and_eligible_donor_pages_are_bounded(admin_client, test_session):
    from app.models.hospital import HospitalDetails
    from tests.helpers import insert_donor

    for n, city in enumerate(["Chennai", "Madurai", "Salem"], 1):
        test_session.add(HospitalDetails(
            id=f"H-{n}", hospital_name=f"Hospital {n}", hospital_address="1 Test Street",
            country="India", state="TN", pincode="600001", city=city,
        ))
        await insert_donor(test_session, n)

    page = {"limit": 1, "offset": 1}
    cities = await admin_client.get("/api/v1/hospitals/cities", params=page)
    assert cities.status_code == 200 and cities.json() == ["Madurai"]
    donors = await admin_client.get("/api/v1/donors/blood-group/O%2B", params=page)
    assert donors.status_code == 200
    assert [row["id"] for row in donors.json()] == ["DON-2"]
    filtered = await admin_client.get("/api/v1/donors/", params={"blood_group": "o+"})
    assert filtered.status_code == 200 and filtered.json()["total"] == 3
