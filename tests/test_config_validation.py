"""B1: weak or placeholder secrets are rejected in every environment; production also needs CAPTCHA."""

import pytest
from pydantic import ValidationError

from app.config import Settings

GOOD_KEY = "0123456789abcdef0123456789abcdef"  # 32 chars, no placeholder words

BASE = dict(
    DATABASE_URL="sqlite+aiosqlite://", GOOGLE_MAPS_API_KEY="x", MAIL_SERVER="x", MAIL_USERNAME="x",
    MAIL_PASSWORD="smtp-password-that-must-not-leak", MAIL_FROM="a@example.com",
)


def build(**overrides) -> Settings:
    # _env_file=None: never read a developer's .env in a unit test
    return Settings(_env_file=None, **{**BASE, "SECRET_KEY": GOOD_KEY, **overrides})


@pytest.mark.parametrize("env", ["development", "test", "staging", "production", "anything"])
def test_a_short_secret_is_rejected_in_every_environment(env):
    extra = dict(RECAPTCHA_SECRET_KEY="r", RECAPTCHA_ENFORCED=True) if env == "production" else {}
    with pytest.raises(ValidationError, match="at least 32 characters"):
        build(APP_ENV=env, SECRET_KEY="short-secret-value-123", **extra)


@pytest.mark.parametrize("placeholder", [
    "your-secret-key-here",
    "your-secret-key-here-padded-to-32-chars!!",
    "CHANGE_ME_CHANGE_ME_CHANGE_ME_CHANGE_ME",
    "changeme-changeme-changeme-changeme-12",
    "replace-me-with-a-generated-key-please",
    "this-is-a-placeholder-value-for-the-key",
])
def test_placeholder_secrets_are_rejected_whatever_their_length(placeholder):
    with pytest.raises(ValidationError, match="placeholder"):
        build(SECRET_KEY=placeholder)


def test_a_generated_key_is_accepted_in_development():
    assert build(APP_ENV="development").SECRET_KEY == GOOD_KEY


def test_the_error_does_not_echo_secrets_or_other_settings():
    with pytest.raises(ValidationError) as caught:
        build(SECRET_KEY="short-secret-value-123")
    text = str(caught.value)
    assert "short-secret-value-123" not in text
    assert "smtp-password-that-must-not-leak" not in text


def test_the_error_tells_you_how_to_fix_it():
    with pytest.raises(ValidationError, match="secrets.token_urlsafe"):
        build(SECRET_KEY="short")


def test_production_requires_recaptcha_secret_and_enforcement():
    with pytest.raises(ValidationError, match="RECAPTCHA_SECRET_KEY"):
        build(APP_ENV="production", RECAPTCHA_ENFORCED=True)
    with pytest.raises(ValidationError, match="RECAPTCHA_ENFORCED"):
        build(APP_ENV="production", RECAPTCHA_SECRET_KEY="r", RECAPTCHA_ENFORCED=False)
    with pytest.raises(ValidationError, match="RECAPTCHA_ENFORCED"):
        build(APP_ENV="production", RECAPTCHA_SECRET_KEY="r")  # the default (false) is not enough
    ok = build(APP_ENV="Production", RECAPTCHA_SECRET_KEY="r", RECAPTCHA_ENFORCED=True)
    assert ok.RECAPTCHA_ENFORCED is True


def test_development_does_not_require_recaptcha():
    ok = build(APP_ENV="development")
    assert ok.RECAPTCHA_ENFORCED is False and ok.RECAPTCHA_SECRET_KEY is None


def test_the_shipped_env_example_fails_loudly_instead_of_running_with_a_placeholder():
    """cp .env.example .env must not give you a working server signing tokens with a public key."""
    from pathlib import Path

    values = {}
    for line in (Path(__file__).resolve().parent.parent / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, **{**BASE, **{k: v for k, v in values.items() if k == "SECRET_KEY"}})


# ------------------------------------------------------------------ B11: docs flag

def test_docs_follow_the_environment_unless_set_explicitly():
    assert build(APP_ENV="development").docs_enabled is True
    prod = dict(RECAPTCHA_SECRET_KEY="r", RECAPTCHA_ENFORCED=True)
    assert build(APP_ENV="production", **prod).docs_enabled is False
    assert build(APP_ENV="production", ENABLE_DOCS=True, **prod).docs_enabled is True
    assert build(APP_ENV="development", ENABLE_DOCS=False).docs_enabled is False
