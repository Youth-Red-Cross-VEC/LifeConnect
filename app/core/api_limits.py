"""Limits for the JSON-only HTTP API, including direct requests without an edge proxy."""
import json
import math
from typing import Never

from fastapi import HTTPException, Request
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_BYTES = 64 * 1024


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    obj = dict(pairs)
    if obj.keys() & {"__proto__", "constructor", "prototype"}:
        raise ValueError("Reserved JSON property")
    if len(obj) != len(pairs):
        raise ValueError("Duplicate JSON property")
    return obj


def _invalid_constant(value: str) -> Never:
    raise ValueError("Invalid JSON constant")


def _validate_json_values(value: object) -> None:
    if isinstance(value, str):
        # PostgreSQL text columns cannot represent NUL or unpaired surrogates.
        if "\x00" in value:
            raise ValueError("Invalid string")
        value.encode("utf-8")
    elif isinstance(value, list):
        for item in value:
            _validate_json_values(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_json_values(key)
            _validate_json_values(item)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite number")


class ApiRequestLimits:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            return await self.app(scope, receive, send)

        async def reject(status: int, message: str) -> None:
            await JSONResponse({"detail": message}, status_code=status)(scope, receive, send)

        if len(scope["query_string"]) > 4096 or len(scope["path"]) > 1024:
            return await reject(414, "Request URL too long")
        if sum(len(k) + len(v) for k, v in scope["headers"]) > 32768:
            return await reject(431, "Request headers too large")
        headers = Headers(scope=scope)
        if any(len(headers.getlist(key)) > 1 for key in ("content-length", "authorization", "content-type")):
            return await reject(400, "Ambiguous request headers")
        size = headers.get("content-length")
        if size is not None:
            if headers.get("transfer-encoding") or not size.isascii() or not size.isdecimal() or len(size) > 19:
                return await reject(400, "Invalid request length")
            if int(size) > MAX_BODY_BYTES:
                return await reject(413, "Request body too large")

        body = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            chunk = event.get("body", b"")
            if len(body) + len(chunk) > MAX_BODY_BYTES:
                return await reject(413, "Request body too large")
            body.extend(chunk)
            if not event.get("more_body", False):
                break
        if size is not None and len(body) != int(size):
            return await reject(400, "Request length mismatch")
        if body:
            media_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if media_type != "application/json" and not (media_type.startswith("application/") and media_type.endswith("+json")):
                return await reject(415, "Expected a JSON request body")
            if headers.get("content-encoding", "identity").lower() != "identity":
                return await reject(415, "Unsupported request encoding")

            try:
                parsed = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
                _validate_json_values(parsed)
                scope["api_body_has_input"] = parsed != {}
            except (ValueError, RecursionError):
                return await reject(400, "Invalid JSON request body")

        delivered = False
        async def replay() -> Message:
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)


async def validate_parameters(request: Request) -> None:
    """All current query parameters are scalars with explicit aliases in the route schema."""
    route = request.scope["route"]
    if request.scope.get("api_body_has_input") and not route.body_field:
        raise HTTPException(422, "This operation does not accept a request body")
    fields = route.dependant.query_params
    allowed = {field.alias for field in fields}
    params = request.query_params
    if any(chr(0) in value for value in (*params.values(), *request.path_params.values())):
        raise HTTPException(422, "Invalid request parameter")
    if len(params.multi_items()) != len(params) or params.keys() - allowed:
        raise HTTPException(422, "Unexpected or repeated query parameter")
