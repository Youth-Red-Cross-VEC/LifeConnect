"""Exercise independent worker pools against an authenticated, disposable Redis process."""
import asyncio
import os
import secrets
import shutil
import socket
import subprocess
import time
from contextlib import contextmanager

import pytest
from pydantic import SecretStr
from fastapi import Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.core.rate_limiter import (
    build_limiter, check_default_api_limit, close_rate_storage,
    enforce_account_limit, setup_rate_limiting,
)


@pytest.fixture
def isolated_store(tmp_path):
    redis = pytest.importorskip("redis")
    binary = os.environ.get("LC_REDIS_TEST_SERVER") or shutil.which("redis-server")
    if not binary:
        pytest.skip("Provide LC_REDIS_TEST_SERVER to run the disposable Redis integration test")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    password = secrets.token_hex(32)
    config = tmp_path / "redis.conf"
    config.write_text(f'bind 127.0.0.1\nport {port}\nrequirepass {password}\nappendonly yes\nsave ""\n')
    uri = SecretStr(f"redis://:{password}@127.0.0.1:{port}/0")
    from redis.backoff import NoBackoff
    from redis.retry import Retry
    inspector = redis.Redis.from_url(uri.get_secret_value(), socket_timeout=1, socket_connect_timeout=0.2,
                                     retry=Retry(NoBackoff(), 0))

    @contextmanager
    def running():
        process = subprocess.Popen([binary, config.name], cwd=tmp_path, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 12
            while process.poll() is None and time.monotonic() < deadline:
                try:
                    if inspector.ping():
                        break
                except (redis.ConnectionError, redis.TimeoutError):
                    time.sleep(0.05)
            else:
                pytest.fail("Disposable Redis failed to start")
            yield
            inspector.shutdown(nosave=True)
            process.wait(timeout=6)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    try:
        yield uri, inspector, running
    finally:
        inspector.close()
        config.unlink()


async def test_shared_budget_outage_restart_and_recovery(isolated_store):
    uri, inspector, running = isolated_store
    accepted = []

    def worker(peer):
        app = FastAPI(dependencies=[Depends(check_default_api_limit)])
        setup_rate_limiting(app)
        app.state.limiter = build_limiter(20, uri.get_secret_value())

        @app.get("/protected")
        async def protected(request: Request, email: str):
            await enforce_account_limit(request, email, "3/minute")
            accepted.append(True)
            return {"ok": True}

        @app.get("/ip-only")
        async def ip_only():
            return {"ok": True}

        return app, AsyncClient(transport=ASGITransport(app=app, client=(peer, 9000)), base_url="http://test")

    app1, first = worker("192.0.2.1")
    app2, second = worker("192.0.2.2")
    account = {"email": "synthetic@example.com"}
    try:
        async with first, second:
            with running():
                responses = await asyncio.gather(*[
                    (first if i % 2 else second).get("/protected", params=account) for i in range(8)
                ])
                assert sorted(r.status_code for r in responses) == [200] * 3 + [429] * 5
                keys = list(inspector.scan_iter())
                assert len(keys) == 3
                assert all(k.startswith(b"lifeconnect:limits:") and 0 < inspector.ttl(k) <= 60 for k in keys)
                assert all(b"192.0.2" not in k and b"synthetic" not in k for k in keys)
                # Reuse the same peer across two independent application pools.
                transport = ASGITransport(app=app2, client=("192.0.2.1", 9001))
                async with AsyncClient(transport=transport, base_url="http://test") as same_peer:
                    results = await asyncio.gather(*[
                        (first if i % 2 else same_peer).get("/ip-only") for i in range(24)
                    ])
                    assert sorted(r.status_code for r in results) == [200] * 20 + [429] * 4
            response = await asyncio.wait_for(first.get("/protected", params=account), timeout=5)
            assert response.status_code == 503
            assert response.json() == {"detail": "Service temporarily unavailable"}
            assert response.headers["retry-after"] == "1"
            assert len(accepted) == 3
            with running():
                assert (await second.get("/protected", params=account)).status_code == 429
                assert (await first.get("/protected", params={"email": "other@example.com"})).status_code == 200
                assert len(accepted) == 4
    finally:
        close_rate_storage(app1.state.limiter)
        close_rate_storage(app2.state.limiter)


@pytest.mark.parametrize("option", ["RATELIMIT_IN_MEMORY_FALLBACK_ENABLED", "RATELIMIT_SWALLOW_ERRORS"])
def test_shared_store_rejects_unsafe_configuration(monkeypatch, option):
    pytest.importorskip("redis")
    monkeypatch.setenv(option, "true")
    with pytest.raises(ValueError, match="without local fallback"):
        build_limiter(5, "redis://localhost/0")
