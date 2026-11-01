"""Runtime dependencies are exactly pinned and the image installs the runtime file only."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
RUNTIME = (ROOT / "requirements.txt").read_text(encoding="utf-8")
DEVELOPMENT = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")


def test_every_runtime_requirement_is_exactly_pinned():
    requirements = [line.strip() for line in RUNTIME.splitlines() if line.strip() and not line.startswith("#")]
    assert requirements
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+(?:\[[^]]+\])?==[0-9][A-Za-z0-9.!+_-]*", line) for line in requirements)


def test_auth_libraries_are_replaced_and_bcrypt_is_supported():
    lowered = RUNTIME.lower()
    assert "pyjwt==2.15.0" in lowered
    assert "bcrypt==4.2.1" in lowered
    assert "python-jose" not in lowered
    assert "passlib" not in lowered
    assert "gunicorn" not in lowered


def test_development_tools_are_separate():
    for package in ("pytest==", "ruff==", "black==", "mypy=="):
        assert package in DEVELOPMENT


def test_docker_installs_the_pinned_runtime_requirements_only():
    assert "COPY requirements.txt ./" in DOCKERFILE
    assert "pip install --no-cache-dir --prefix=/install -r requirements.txt" in DOCKERFILE
    assert "COPY requirements-dev.txt" not in DOCKERFILE
    assert "requirements-runtime.lock" not in DOCKERFILE


def test_ci_audits_the_runtime_requirements():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "pip-audit -r requirements.txt" in ci
