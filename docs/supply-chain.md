# Supply chain: what is pinned, and what still needs pinning

## Already pinned

| What | Where | How |
| ---- | ----- | --- |
| Python packages in the API image | `requirements-runtime.lock` | Every package and transitive package at an exact version with `--hash=sha256:` lines. The Dockerfile installs with `--require-hashes --no-deps`, so nothing is resolved at build time and a file whose hash is not in the lock is refused. |
| `uv` (the installer) | `Dockerfile` | `COPY --from=ghcr.io/astral-sh/uv:0.12.23@sha256:...` (version **and** digest), plus a build step that fails if `uv --version` is not `0.12.23`. The old `curl ... \| sh` is gone, and so is `curl` from the build stage. |
| Frontend packages | `frontend/package-lock.json` | `npm ci --ignore-scripts` in `frontend/Dockerfile`. |
| Dependency audit in CI | `.github/workflows/ci.yml` | `pip-audit` runs on `requirements-runtime.lock` (what the image really installs) as well as `requirements.txt`; `npm audit` runs on production dependencies; Trivy scans the built image. |

The one ignored advisory is `PYSEC-2026-1325` (CVE-2024-23342, a timing attack on ECDSA P-256 signing in
`python-ecdsa`, no fixed release). It is only a dependency of `python-jose` and is unused: tokens are signed with
HS256. Remove the ignore when a fix exists. Moving from `python-jose` to PyJWT would remove the package entirely
(a dependency change, so it was not done here).

## Updating the Python dependencies

1. Edit `requirements-runtime.in`.
2. Regenerate the lock with the same `uv` version the Dockerfile uses (the command is at the top of
   `requirements-runtime.in`).
3. `docker build .` and run the tests, then commit both files.

## Updating uv

Change the tag in `Dockerfile`, look up the new digest, update the version check and the `uv==` line in
`requirements-runtime.in`, and regenerate the lock:

```bash
docker buildx imagetools inspect ghcr.io/astral-sh/uv:<new version> --format '{{.Manifest.Digest}}'
```

## Still to pin (needs a lookup only you should do)

These were deliberately **not** pinned by guesswork: a wrong SHA or digest would break the build, and an invented
one is worse than none. Pinning turns a mutable tag into an exact, reviewable version. Dependabot (configured in
`.github/dependabot.yml` for `github-actions` and `docker`) then proposes updates to the pinned value.

### GitHub Actions (`.github/workflows/ci.yml`)

Replace each tag with the full 40-character commit SHA and keep the tag in a trailing comment:

| Action | Used at |
| ------ | ------- |
| `actions/checkout@v4` | lines 28, 45, 59, 84 |
| `actions/setup-python@v5` | lines 29, 60 |
| `actions/setup-node@v4` | lines 46, 74 |
| `aquasecurity/trivy-action@0.28.0` | line 86 |

Look up the commit a tag points to (works without logging in; for an annotated tag the `^{}` line is the commit,
otherwise the first line is):

```bash
git ls-remote https://github.com/actions/checkout "refs/tags/v4" "refs/tags/v4^{}"
git ls-remote https://github.com/actions/setup-python "refs/tags/v5" "refs/tags/v5^{}"
git ls-remote https://github.com/actions/setup-node "refs/tags/v4" "refs/tags/v4^{}"
git ls-remote https://github.com/aquasecurity/trivy-action "refs/tags/0.28.0" "refs/tags/0.28.0^{}"
```

or, if you are logged in to the GitHub CLI: `gh api repos/actions/checkout/commits/v4 --jq .sha`.
The result goes into `uses: actions/checkout@<40-char sha> # v4`.

### Base images

Append `@sha256:<digest>` to each reference (keep the tag before it so humans can read it):

| Image | Used in |
| ----- | ------- |
| `python:3.11-alpine` | `Dockerfile` (builder and runtime stages) |
| `node:20-alpine` | `frontend/Dockerfile` |
| `nginx:stable-alpine` | `frontend/Dockerfile` |
| `postgres:16-alpine` | `docker-compose.yml`, `.github/workflows/ci.yml` (service container) |

```bash
docker buildx imagetools inspect python:3.11-alpine --format '{{.Manifest.Digest}}'
docker buildx imagetools inspect node:20-alpine --format '{{.Manifest.Digest}}'
docker buildx imagetools inspect nginx:stable-alpine --format '{{.Manifest.Digest}}'
docker buildx imagetools inspect postgres:16-alpine --format '{{.Manifest.Digest}}'
```

This gives the digest of the multi-architecture index, which is what you want in a Dockerfile `FROM` line.
`nginx:stable-alpine` and `python:3.11-alpine` are moving tags: pinning them means you take security updates by
merging Dependabot's pull request instead of automatically on the next build. That is the point, but it only helps
if those pull requests are reviewed and merged.
