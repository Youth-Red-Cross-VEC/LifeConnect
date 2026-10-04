"""P2-42: LIKE wildcards in public search are matched literally."""

import pytest
from httpx import AsyncClient

from app.models.hospital import HospitalDetails
from app.utils.search import escape_like


def _hospital(n: int, name: str) -> HospitalDetails:
    return HospitalDetails(
        id=f"H-{n}", hospital_name=name, hospital_address="1 Road", pincode="600001",
        city="Chennai", state="TN", country="India",
    )


def test_escape_like():
    assert escape_like("50%_off\\") == "50\%\_off\\\\"
    assert escape_like("plain") == "plain"


@pytest.mark.asyncio
@pytest.mark.parametrize("term,expected", [("%", {"100% Care"}), ("_", {"Alpha_Beta"}), ("Care", {"100% Care"})])
async def test_hospital_search_treats_wildcards_literally(client: AsyncClient, test_session, term, expected):
    test_session.add_all([_hospital(1, "100% Care"), _hospital(2, "Alpha_Beta"), _hospital(3, "Plain Clinic")])
    await test_session.commit()
    r = await client.get("/api/v1/hospitals/", params={"search": term})
    assert r.status_code == 200
    assert {h["hospital_name"] for h in r.json()["items"]} == expected


