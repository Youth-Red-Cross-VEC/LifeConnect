"""B16: the Docker build contexts must not carry secrets or personal data, yet contain what the Dockerfiles COPY."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _patterns(context: Path) -> list[str]:
    lines = (context / ".dockerignore").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def _regex(pattern: str) -> re.Pattern:
    """Docker's .dockerignore globbing: patterns are anchored at the context root; ** crosses directories."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out))


def excluded(path: str, patterns: list[str]) -> bool:
    """Last matching pattern wins; a pattern that matches a parent directory excludes everything below it."""
    result = False
    parts = path.split("/")
    prefixes = ["/".join(parts[: n + 1]) for n in range(len(parts))]
    for pattern in patterns:
        negate = pattern.startswith("!")
        regex = _regex(pattern.lstrip("!").rstrip("/"))
        if any(regex.fullmatch(p) for p in prefixes):
            result = not negate
    return result


def test_the_matcher_follows_dockerignore_rules():
    p = ["node_modules", "**/node_modules", ".env*", "!.env.keep", "docs"]
    assert excluded("node_modules/a/b.js", p) and excluded("frontend/node_modules/x.js", p)
    assert excluded(".env", p) and excluded(".env.local", p) and not excluded(".env.keep", p)
    assert excluded("docs/setup.md", p) and not excluded("app/docs.py", p) and not excluded("src/node_modules_x.js", p)


# ------------------------------------------------------------------ API image (context: repository root)

API_PATTERNS = _patterns(ROOT) if (ROOT / ".dockerignore").exists() else []


@pytest.mark.parametrize("path", [
    ".git/config", ".github/workflows/ci.yml", ".env", ".env.local", ".env.production", ".env.example",
    "frontend/.env", "frontend/node_modules/react/index.js", "frontend/dist/index.html",
    "venv/pyvenv.cfg", ".venv/pyvenv.cfg",
    "source_db.sql", "docs/initial_data.sql", "docs/SyntheticData.sql", "backup.dump", "export.sql",
    "app/static/images/certificates/Asha_20261005_120000_certificate.png",
    "app/static/images/certificates/Asha_20261005_120000_1a2b3c4d_certificate.txt",
    "LifeConnect analysis.pdf", "AUDIT_STATUS.md", "FIX_LOG.md",
    "tests/conftest.py", "graphify-out/graph.json", ".pytest_cache/v/cache/nodeids",
    "app/__pycache__/main.cpython-314.pyc",
    "app/seed.sql", "scripts/export.dump", "migrations/old.bak",  # nested dumps are caught too
])
def test_the_api_context_leaves_out(path):
    assert excluded(path, API_PATTERNS), f"{path} would be sent to the build daemon"


def _copy_sources(dockerfile: Path) -> list[str]:
    sources = []
    for line in dockerfile.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if parts and parts[0].upper() == "COPY" and not any(p.startswith("--from") for p in parts):
            args = [p for p in parts[1:] if not p.startswith("--")]
            sources += args[:-1]
    return sources


def _files(context: Path, source: str) -> list[str]:
    base = context / source
    if base.is_file():
        return [source]
    return [
        p.relative_to(context).as_posix() for p in base.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    ]


def test_everything_the_api_dockerfile_copies_is_in_the_context():
    sources = _copy_sources(ROOT / "Dockerfile")
    assert {"app/", "alembic.ini", "migrations/"} <= set(sources)
    missing = []
    for source in sources:
        for path in _files(ROOT, source.rstrip("/")):
            # generated certificates hold donor names and are runtime data, never image content
            if "static/images/certificates/" in path:
                continue
            if excluded(path, API_PATTERNS):
                missing.append(path)
    assert missing == [], f"the Dockerfile COPYs these but .dockerignore removes them: {missing[:10]}"


# ------------------------------------------------------------------ frontend image (context: ./frontend)

FRONTEND = ROOT / "frontend"
FRONTEND_PATTERNS = _patterns(FRONTEND)


@pytest.mark.parametrize("path", [
    ".env", ".env.local", ".env.production", ".env.example", "node_modules/react/index.js",
    "dist/index.html", ".git/config", "debug.log",
])
def test_the_frontend_context_leaves_out(path):
    assert excluded(path, FRONTEND_PATTERNS), f"{path} would be sent to the build daemon"


def test_the_frontend_build_inputs_are_in_the_context():
    needed = ["package.json", "package-lock.json", "index.html", "vite.config.js", "nginx.conf",
              "security-headers.conf", "src/main.jsx", "src/App.jsx"]
    needed += [p.relative_to(FRONTEND).as_posix() for p in (FRONTEND / "public").rglob("*") if p.is_file()][:5]
    assert [p for p in needed if excluded(p, FRONTEND_PATTERNS)] == []
    assert {"package.json", "package-lock.json", "nginx.conf", "security-headers.conf"} <= set(
        _copy_sources(FRONTEND / "Dockerfile")
    ) | {"."}


@pytest.mark.parametrize("path", [
    "nested/.env.staging", "nested/export.sql.gz", "nested/archive.dump.gz",
    "nested/records.sqlite", "nested/records.db", "nested/credentials.p12",
    "nested/private.pem", "nested/archive.backup.gz",
])
@pytest.mark.parametrize("patterns", [API_PATTERNS, FRONTEND_PATTERNS])
def test_sensitive_files_are_excluded_from_both_build_contexts(path, patterns):
    assert excluded(path, patterns)
