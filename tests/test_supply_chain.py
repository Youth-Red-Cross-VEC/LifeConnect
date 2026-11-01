"""B17: the API image installs a hash-pinned dependency set with a version-pinned installer, and CI audits that set."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
LOCK = ROOT / "requirements-runtime.lock"
SOURCE = ROOT / "requirements-runtime.in"


def _requirement_blocks(text: str) -> dict[str, str]:
    """{normalised name: the lock lines for that requirement}."""
    blocks, name = {}, None
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==(\S+)", line)
        if match:
            name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
            blocks[name] = line
        elif name and line.startswith("    "):
            blocks[name] += "\n" + line
    return blocks


def _wanted() -> list[str]:
    names = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            names.append(re.sub(r"[-_.]+", "-", re.split(r"[\[<>=!~ ]", line)[0]).lower())
    return names


# ------------------------------------------------------------------ the installer

def test_uv_is_not_fetched_by_piping_a_script_into_a_shell():
    assert not re.search(r"curl[^\n]*\|\s*(ba)?sh", DOCKERFILE)
    assert "astral.sh/uv/install.sh" not in DOCKERFILE


def test_uv_comes_from_a_version_pinned_image_that_is_verified():
    match = re.search(r"COPY --from=ghcr\.io/astral-sh/uv:(\d+\.\d+\.\d+)(@sha256:[0-9a-f]{64})? ", DOCKERFILE)
    assert match, "pin uv to an exact version (never :latest)"
    assert f"uv {match.group(1)}" in DOCKERFILE, "the build should assert it got the version it asked for"
    assert f"uv=={match.group(1)}" in SOURCE.read_text(encoding="utf-8"), "docs and Dockerfile must name one version"


# ------------------------------------------------------------------ the dependency set

def test_the_image_installs_from_the_hashed_lock_only():
    install = re.search(r"RUN uv pip install[^\n]*(?:\\\n[^\n]*)*", DOCKERFILE).group(0)
    assert "--require-hashes" in install
    assert "-r requirements-runtime.lock" in install
    assert "--no-deps" in install, "every transitive package must come from the lock, none resolved at build time"
    assert not re.search(r"\bfastapi\b", install), "no bare package list"


def test_every_locked_package_is_pinned_and_hashed():
    blocks = _requirement_blocks(LOCK.read_text(encoding="utf-8"))
    assert len(blocks) > 20
    unhashed = [name for name, block in blocks.items() if "--hash=sha256:" not in block]
    assert unhashed == []
    for block in blocks.values():
        for digest in re.findall(r"--hash=sha256:([0-9a-f]+)", block):
            assert len(digest) == 64


def test_the_lock_covers_every_package_the_image_is_meant_to_have():
    blocks = _requirement_blocks(LOCK.read_text(encoding="utf-8"))
    missing = [name for name in _wanted() if name not in blocks]
    assert missing == []
    assert blocks["bcrypt"].startswith("bcrypt==3."), "passlib 1.7 needs bcrypt < 4"


def test_the_lock_is_not_stale():
    header = LOCK.read_text(encoding="utf-8").split("\n", 3)[1]
    assert "requirements-runtime.in" in header and "--generate-hashes" in header


def test_the_dockerfile_does_not_need_curl_any_more():
    builder_packages = re.search(r"RUN apk add --no-cache \\\n((?:\s+[^\n]*\\\n)*\s+[^\n]*)\n", DOCKERFILE).group(1)
    assert not re.search(r"^\s*curl\b", builder_packages, re.M)


# ------------------------------------------------------------------ CI

def test_ci_audits_what_the_image_installs():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "pip-audit" in ci and "requirements-runtime.lock" in ci
