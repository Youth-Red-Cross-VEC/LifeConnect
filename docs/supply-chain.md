# Dependency management

`requirements.txt` and `requirements-redis.txt` are the pinned runtime inputs installed by the API Dockerfile. Development and test
packages are pinned separately in `requirements-dev.txt`; install that file locally to run the suite.
`pip-audit -r requirements.txt -r requirements-redis.txt` audits the production set. The frontend uses `package-lock.json`, `npm ci`,
and `npm audit`.

To upgrade a Python dependency, update its exact pin in `requirements.txt`, keep `pyproject.toml` in sync,
regenerate `uv.lock` using `uv lock`, update any affected tests, and run the backend test suite and dependency audit. Update the
Docker image and CI in the same change. Do not add broad unpinned package lists to the runtime image.

The Dockerfile tracks Python 3.11 Alpine patches and runs the app as `appuser`. CI checks both built images with
Trivy and fails on high or critical results, including findings with no published fix. CI also checks Git
history and the current checkout with Gitleaks. Both scanner binaries are verified by SHA-256 before use.
Update the version and the reviewed checksum together. GitHub Actions use full commit pins and read-only
repository access. Inspect the [Trivy release](https://github.com/aquasecurity/trivy/releases/tag/v0.76.2)
and [Gitleaks release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1) when updating those pins.
