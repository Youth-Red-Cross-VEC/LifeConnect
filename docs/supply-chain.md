# Dependency management

`requirements.txt` is the exact, pinned runtime set installed by the API Dockerfile. Development and test
packages are pinned separately in `requirements-dev.txt`; install that file locally to run the suite.
`pip-audit -r requirements.txt` audits the production set. The frontend uses `package-lock.json`, `npm ci`,
and `npm audit`.

To upgrade a Python dependency, update its exact pin in `requirements.txt`, keep `pyproject.toml` in sync,
update any affected tests, and run the backend test suite plus `pip-audit -r requirements.txt`. Update the
Docker image and CI in the same change. Do not add broad unpinned package lists to the runtime image.

The Dockerfile uses pinned Python image tags and the `requirements.txt` pins, then runs the app as `appuser`.
Review base-image and GitHub Action updates regularly so security fixes reach production.
