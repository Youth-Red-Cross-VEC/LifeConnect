"""Shipped .env.example must not weaken security defaults."""

from pathlib import Path

ENV = {}
for line in (Path(__file__).resolve().parent.parent / ".env.example").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        ENV[key.strip()] = value.strip()


def test_access_token_lifetime_is_short():
    assert int(ENV["ACCESS_TOKEN_EXPIRE_MINUTES"]) <= 60
