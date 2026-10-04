"""API contract snapshot (P3-56).

The public contract (operations, parameters, request/response schemas and their fields) is
snapshotted in tests/contract/openapi_snapshot.json. Any change to it fails this test until the
snapshot is regenerated on purpose:

    UPDATE_API_SNAPSHOT=1 python -m pytest tests/test_api_contract.py

The frontend and external clients depend on this surface, so review the snapshot diff in the PR.
"""

import json
import os
from pathlib import Path

from app.main import app

SNAPSHOT = Path(__file__).parent / "contract" / "openapi_snapshot.json"
METHODS = {"get", "post", "put", "patch", "delete"}


def _ref_name(schema: dict | None) -> str | None:
    if not schema:
        return None
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if schema.get("type") == "array":
        return f"array<{_ref_name(schema.get('items')) or schema.get('items', {}).get('type')}>"
    if "anyOf" in schema:
        return "|".join(sorted(filter(None, (_ref_name(s) or s.get("type") for s in schema["anyOf"]))))
    return schema.get("type")


def _field_type(schema: dict) -> str:
    return _ref_name(schema) or "any"


def build_contract() -> dict:
    spec = app.openapi()
    operations = {}
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            if method not in METHODS:
                continue
            body = op.get("requestBody", {}).get("content", {})
            body_schema = next(iter(body.values()), {}).get("schema") if body else None
            responses = {}
            for code, resp in op.get("responses", {}).items():
                content = resp.get("content", {}).get("application/json", {})
                responses[code] = _ref_name(content.get("schema"))
            operations[f"{method.upper()} {path}"] = {
                "secured": bool(op.get("security")),
                "params": sorted(
                    f"{p['in']}:{p['name']}:{'required' if p.get('required') else 'optional'}"
                    for p in op.get("parameters", [])
                ),
                "body": _ref_name(body_schema),
                "responses": dict(sorted(responses.items())),
            }
    schemas = {}
    for name, schema in spec.get("components", {}).get("schemas", {}).items():
        required = set(schema.get("required", []))
        schemas[name] = {
            prop: f"{_field_type(defn)}{'' if prop in required else '?'}"
            for prop, defn in sorted(schema.get("properties", {}).items())
        }
    return {"operations": dict(sorted(operations.items())), "schemas": dict(sorted(schemas.items()))}


def test_api_contract_matches_snapshot():
    current = build_contract()
    if os.environ.get("UPDATE_API_SNAPSHOT") == "1":
        SNAPSHOT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert current == expected, "API contract changed; if intended run with UPDATE_API_SNAPSHOT=1"


def test_snapshot_covers_the_core_surface():
    ops = build_contract()["operations"]
    for key in ("POST /api/v1/auth/donor/login", "POST /api/v1/auth/refresh", "POST /api/v1/auth/logout",
                "POST /api/v1/blood-requests/", "POST /api/v1/certificates/generate"):
        assert key in ops
