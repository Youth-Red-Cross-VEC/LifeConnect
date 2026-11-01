"""Shipped .env.example must not weaken security defaults."""

from pathlib import Path

ENV = {}
for line in (Path(__file__).resolve().parent.parent / ".env.example").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        ENV[key.strip()] = value.strip()


def test_access_token_lifetime_is_short():
    assert int(ENV["ACCESS_TOKEN_EXPIRE_MINUTES"]) <= 60


def test_every_setting_is_documented_in_env_example():
    """A new Settings field must show up in .env.example (commented out is fine for optional ones)."""
    import re

    from app.config import Settings

    text = (Path(__file__).resolve().parent.parent / ".env.example").read_text(encoding="utf-8")
    documented = set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", text, re.M))
    missing = sorted(set(Settings.model_fields) - documented)
    assert not missing, f"add these to .env.example: {missing}"


def test_example_secret_is_an_obvious_placeholder_and_compose_password_is_not_a_default():
    assert ENV["SECRET_KEY"] == "CHANGE_ME"
    assert ENV["POSTGRES_PASSWORD"].startswith("CHANGE_ME")
    assert ENV["RECAPTCHA_ENFORCED"] == "false"  # development default; production is forced by config validation
