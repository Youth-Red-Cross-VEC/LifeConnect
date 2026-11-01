"""RATE_LIMIT_STORAGE_URI=redis://... must fail fast, naming requirements-redis.txt, when redis is missing."""

import importlib.util
from pathlib import Path

import pytest

from app.core import rate_limiter
from app.core.rate_limiter import build_limiter


def _pretend_redis_missing(monkeypatch):
    real = importlib.util.find_spec
    monkeypatch.setattr(
        rate_limiter.importlib.util, "find_spec", lambda name, *a, **k: None if name == "redis" else real(name, *a, **k)
    )


@pytest.mark.parametrize("uri", ["redis://localhost:6379/0", "rediss://user:secret@host:6380/1"])
def test_redis_uri_without_package_fails_with_clear_message(monkeypatch, uri):
    _pretend_redis_missing(monkeypatch)
    with pytest.raises(RuntimeError) as error:
        build_limiter(60, uri)
    message = str(error.value)
    assert "requirements-redis.txt" in message
    assert "secret" not in message, "credentials in the URI must not be echoed"


def test_memory_storage_never_needs_redis(monkeypatch):
    _pretend_redis_missing(monkeypatch)
    assert build_limiter(60, "memory://") is not None


def test_requirements_redis_file_exists_and_main_requirements_do_not_list_redis():
    root = Path(__file__).resolve().parent.parent
    assert "redis" in (root / "requirements-redis.txt").read_text(encoding="utf-8")
    for name in ("requirements.txt", "pyproject.toml"):
        lines = (root / name).read_text(encoding="utf-8").lower().splitlines()
        assert not [l for l in lines if l.strip().strip('",').startswith("redis")], name
