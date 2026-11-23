"""A3, A4, B9: deployment files must not expose the database, must pin the trusted proxy, and must ship SPA headers."""

import re
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from fastapi import Response
from httpx import ASGITransport, AsyncClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.auth.router import _set_refresh_cookie
from app.main import app
from tests.test_config_validation import build

ROOT = Path(__file__).resolve().parent.parent
LOGIN = "/api/v1/auth/donor/login"


def _load(name: str) -> dict:
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


def _env(service: dict) -> dict:
    env = service.get("environment", [])
    if isinstance(env, dict):
        return {k: str(v) for k, v in env.items()}
    return dict(item.split("=", 1) for item in env)


def _default_of(value: str) -> str:
    """'${NAME:-default}' -> 'default'; a literal stays as is."""
    m = re.fullmatch(r"\$\{[A-Z_]+:-([^}]*)\}", value)
    return m.group(1) if m else value


def _published(service: dict) -> list[str]:
    return [str(p) for p in service.get("ports", [])]


# ---------------------------------------------------------------- A3: client IP behind nginx

def _trusted_proxy_ip() -> str:
    compose = _load("docker-compose.yml")
    return _default_of(_env(compose["services"]["api"])["FORWARDED_ALLOW_IPS"])


def test_only_the_pinned_nginx_container_is_a_trusted_proxy():
    compose = _load("docker-compose.yml")
    trusted = _trusted_proxy_ip()
    assert trusted != "*", "trusting every peer lets any client spoof X-Forwarded-For"
    assert re.fullmatch(r"\d+\.\d+\.\d+\.\d+", trusted), "trust one address, not a subnet or a list"

    nginx_ip = compose["services"]["frontend"]["networks"]["default"]["ipv4_address"]
    assert nginx_ip == trusted, "the trusted address must be the frontend (nginx) container's pinned address"
    subnet = compose["networks"]["default"]["ipam"]["config"][0]["subnet"]
    assert nginx_ip.rsplit(".", 1)[0] == subnet.rsplit(".", 1)[0]


def test_uvicorn_runs_with_proxy_headers_enabled():
    compose = _load("docker-compose.yml")
    assert "--proxy-headers" in compose["services"]["api"]["command"]
    assert "--proxy-headers" in (ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_nginx_replaces_spoofable_forwarding_headers_with_connection_values():
    conf = (ROOT / "frontend" / "nginx-site.conf").read_text(encoding="utf-8")
    assert "proxy_set_header X-Forwarded-For $remote_addr;" in conf
    assert "$proxy_add_x_forwarded_for" not in conf
    assert "proxy_set_header Forwarded \"\";" in conf
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in conf


async def _attempts(wrapped_app, peer: str, forwarded_for: list[str]) -> list[int]:
    transport = ASGITransport(app=wrapped_app, client=(peer, 40000))
    codes = []
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        for xff in forwarded_for:
            r = await c.post(
                LOGIN,
                json={"email": "nobody@example.com", "password": "Wrong123"},
                headers={"X-Forwarded-For": xff},
            )
            codes.append(r.status_code)
    return codes


@pytest.mark.asyncio
async def test_two_clients_behind_nginx_get_separate_rate_limit_buckets(client):
    wrapped = ProxyHeadersMiddleware(app, trusted_hosts=_trusted_proxy_ip())
    nginx = _trusted_proxy_ip()

    noisy = await _attempts(wrapped, nginx, ["203.0.113.10"] * 8)
    quiet = await _attempts(wrapped, nginx, ["203.0.113.20"])

    assert 429 in noisy, "the login limit must still trip for one client"
    assert quiet == [401], "a different client must not inherit the noisy client's exhausted budget"


@pytest.mark.asyncio
async def test_spoofed_forwarded_for_from_an_untrusted_peer_is_ignored(client):
    wrapped = ProxyHeadersMiddleware(app, trusted_hosts=_trusted_proxy_ip())

    # A client that talks to the API directly and rotates X-Forwarded-For must not dodge the limit.
    codes = await _attempts(wrapped, "198.51.100.77", [f"203.0.113.{i}" for i in range(1, 9)])

    assert 429 in codes


# ---------------------------------------------------------------- A4: compose exposure

def test_database_is_not_published_by_the_base_compose_file():
    compose = _load("docker-compose.yml")
    assert not _published(compose["services"]["postgres"])


def test_nothing_but_the_frontend_is_published_beyond_loopback():
    compose = _load("docker-compose.yml")
    for name, service in compose["services"].items():
        for port in _published(service):
            if name == "frontend":
                continue  # the intended public entry point
            assert port.startswith("127.0.0.1:"), f"{name} publishes {port} on every interface"


def test_postgres_password_is_required_everywhere_it_is_used():
    compose = _load("docker-compose.yml")
    assert _env(compose["services"]["postgres"])["POSTGRES_PASSWORD"].startswith("${POSTGRES_PASSWORD:?")
    for name in ("api", "scheduler"):
        url = _env(compose["services"][name])["DATABASE_URL"]
        assert "${POSTGRES_PASSWORD:?" in url, f"{name} would start with an empty database password"


def test_dev_override_publishes_only_on_loopback():
    dev = _load("docker-compose.dev.yml")
    published = [p for s in dev["services"].values() for p in _published(s)]
    assert published, "the dev override exists to publish postgres/api for local debugging"
    assert all(p.startswith("127.0.0.1:") for p in published)


# ---------------------------------------------------------------- B9: SPA security headers

def _snippet() -> str:
    return (ROOT / "frontend" / "security-headers.conf").read_text(encoding="utf-8")


def test_spa_pages_and_assets_carry_the_security_headers():
    conf = (ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    prod = (ROOT / "frontend" / "nginx-production.conf.template").read_text(encoding="utf-8")
    site = (ROOT / "frontend" / "nginx-site.conf").read_text(encoding="utf-8")
    assert "include snippets/site.conf;" in conf and "include snippets/site.conf;" in prod
    assert "include snippets/security-headers.conf;" in site.split("location")[0]
    assert "add_header" not in site.split("location / {")[1], "SPA and assets must inherit server headers"
    assert "server_tokens off;" in conf
    for name in (
        "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy",
        "Content-Security-Policy",
    ):
        assert re.search(rf"add_header {name} .* always;", _snippet()), f"{name} missing"
    upstream = (ROOT / "frontend" / "nginx-upstream.conf").read_text(encoding="utf-8")
    assert 'default "";' in upstream and 'https "max-age=31536000";' in upstream
    assert "add_header Strict-Transport-Security $lifeconnect_hsts always;" in _snippet()
    assert "proxy_hide_header Strict-Transport-Security;" in site


def test_csp_is_strict_and_allows_exactly_the_origins_the_frontend_uses():
    csp = re.search(r'add_header Content-Security-Policy "([^"]+)" always;', _snippet()).group(1)
    directives = {d.split()[0]: d.split()[1:] for d in (x.strip() for x in csp.split(";")) if d}

    assert directives["default-src"] == ["'self'"]
    assert directives["object-src"] == ["'none'"]
    assert directives["base-uri"] == ["'self'"]
    assert directives["frame-ancestors"] == ["'none'"]
    assert "'unsafe-eval'" not in csp and "'unsafe-inline'" not in directives["script-src"]
    assert "*" not in " ".join(sum(directives.values(), []))

    assert "https://www.google.com/recaptcha/" in directives["script-src"]
    assert "https://www.gstatic.com/recaptcha/" in directives["script-src"]
    assert "https://www.google.com/recaptcha/" in directives["frame-src"]
    assert "https://fonts.googleapis.com" in directives["style-src"]
    assert "https://cdnjs.cloudflare.com" in directives["style-src"]
    assert "https://fonts.gstatic.com" in directives["font-src"]
    assert "https://cdnjs.cloudflare.com" in directives["font-src"]
    assert directives["connect-src"] == ["'self'", "https://www.google.com/recaptcha/"]


def test_frontend_image_ships_the_snippet():
    dockerfile = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    assert "security-headers.conf /etc/nginx/snippets/security-headers.conf" in dockerfile


class ComposeLoader(yaml.SafeLoader):
    pass


ComposeLoader.add_constructor("!override", lambda loader, node: loader.construct_sequence(node))


def test_production_overlay_exposes_only_the_tls_edge_and_keeps_state_private():
    overlay = yaml.load((ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8"), Loader=ComposeLoader)
    services = overlay["services"]
    assert _published(services["frontend"]) == ["80:80", "443:443"]
    for name in ("api", "scheduler", "postgres", "redis"):
        assert not _published(services[name])
    assert services["postgres"]["networks"] == services["redis"]["networks"] == ["data"]
    assert overlay["networks"]["data"]["internal"] is True
    assert _env(services["api"])["APP_ENV"] == "production"
    assert _env(services["api"])["RATE_LIMIT_STORAGE_URI"] == "redis://redis:6379/0"
    assert services["frontend"]["volumes"][0]["read_only"] is True
    assert services["frontend"]["build"]["args"]["VITE_RECAPTCHA_SITE_KEY"].startswith(
        "${VITE_RECAPTCHA_SITE_KEY:?"
    )


def test_production_tls_template_pins_protocols_certificate_and_redirect_host():
    conf = (ROOT / "frontend" / "nginx-production.conf.template").read_text(encoding="utf-8")
    assert "return 308 https://${LIFECONNECT_DOMAIN}$request_uri;" in conf
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in conf
    assert "ssl_reject_handshake on;" in conf
    assert "ssl_certificate /etc/nginx/tls/fullchain.pem;" in conf
    assert "ssl_certificate_key /etc/nginx/tls/privkey.pem;" in conf


@pytest.mark.parametrize("environment,secure", [("production", True), ("development", False)])
def test_refresh_cookie_matches_transport_and_is_http_only(monkeypatch, environment, secure):
    monkeypatch.setattr(import_module("app.api.auth.router"), "get_settings", lambda: SimpleNamespace(
        APP_ENV=environment, REFRESH_TOKEN_EXPIRE_DAYS=7,
    ))
    response = Response()
    _set_refresh_cookie(response, "synthetic-test-token")
    attributes = {v.strip().lower() for v in response.headers["set-cookie"].split(";")[1:]}
    expected_path = "path=/" if secure else "path=/api/v1/auth"
    assert {"httponly", "samesite=strict", expected_path} <= attributes
    assert response.headers["set-cookie"].startswith("__Host-") is secure
    assert not any(value.startswith("domain=") for value in attributes)
    assert ("secure" in attributes) is secure


PROD = dict(APP_ENV="production", RECAPTCHA_SECRET_KEY="r", RECAPTCHA_ENFORCED=True,
            RATE_LIMIT_STORAGE_URI="redis://redis:6379/0")


def test_production_defaults_to_same_origin_and_accepts_explicit_https_origins():
    assert build(**PROD).ALLOWED_ORIGINS == []
    assert build(**PROD, ALLOWED_ORIGINS=["https://portal.example.test"]).ALLOWED_ORIGINS == [
        "https://portal.example.test"
    ]
    assert "http://localhost:5173" in build(APP_ENV="development").ALLOWED_ORIGINS


@pytest.mark.parametrize("origin", ["*", "http://localhost:5173", "https://*.example.test",
                                      "https://portal.example.test/path", "https://u@portal.example.test"])
def test_production_rejects_overbroad_or_invalid_cors(origin):
    with pytest.raises(ValueError, match="exact HTTPS origins"):
        build(**PROD, ALLOWED_ORIGINS=[origin])


def test_production_rejects_debug():
    with pytest.raises(ValueError, match="DEBUG must be false"):
        build(**PROD, DEBUG=True)
