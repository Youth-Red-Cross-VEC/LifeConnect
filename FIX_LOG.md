# FIX_LOG

Untracked working log for the audit fixes. **Nothing here is committed, staged or pushed.** Source: the
source-only audit `REPORT.md` (it lives in `C:\Users\harsh\security-audit-skill\LifeConnect\run-1\`, not in the
project root as the brief said; it was neither copied nor edited), run against `3fad7fd` on a dirty tree. Every
item was re-verified against the CURRENT code first.

## Baseline (before any change), `3fad7fd` + 33 dirty paths

| Check | Result |
|---|---|
| Backend `pytest -q` (SQLite) | 218 passed, 2 skipped (the 2 skips are the Postgres-only tests) |
| Backend with a throwaway Postgres (`MIGRATION_TEST_DATABASE_URL`) on `tests/test_migrations.py tests/test_scheduler.py` | 7 passed, 0 skipped |
| Frontend `npm run lint` | clean |
| Frontend `npm run build` | passes (chunk-size warning only) |
| Frontend `npm test` | 26 pass |
| Docker | available (29.8.1). Used for: a throwaway Postgres (`lc-test-pg`, 127.0.0.1 only), `docker compose config`, `nginx -t`, real image builds, build-context listings, an isolated compose stack with throwaway secrets. All torn down afterwards. |

A container `lc-migrate-pg` (postgres on 0.0.0.0:55432) already existed from an earlier session. It is not mine and
was left untouched; my tests authenticate with their own throwaway credentials, which that container would reject.

## Final results (after all changes)

| Check | Baseline | After |
|---|---|---|
| Backend `pytest` with a throwaway Postgres | 218 passed, 2 skipped (SQLite only) | **501 passed, 1 skipped** (the skip is a Windows-only filename test) |
| Backend from a fresh venv + `cp .env.example .env`, no Postgres | n/a | 492 passed, 9 skipped (Postgres-only tests and the Windows one) |
| Frontend lint / build / `npm test` | clean / ok / 26 pass | clean / ok / **31 pass** |
| `npm audit` (all, production) | not run | 0 vulnerabilities |
| Tests collected | 220 | 502 |

See "Verification" at the bottom for everything else that was run, and what was not.

## Item table

Status: **fixed** = reproduced by a failing test first, then fixed. Test file names are under `tests/` unless noted.

| Item | Status | Files changed | Tests | Result |
|---|---|---|---|---|
| **A1** reset/deactivation must revoke sessions | fixed | `app/services/refresh_session_service.py` (`revoke_all_for_user`), `app/api/auth/router.py`, `app/api/v1/admins.py`, `app/api/v1/donors.py` | `test_session_revocation.py` (6) | red on old code (old refresh token returned 200); green |
| **A2** queries owned by unverified email | fixed | `app/models/query.py`, migration `0007`, `app/api/auth/deps.py` (`get_optional_donor_id`), `app/api/v1/queries.py`, `app/repositories/query.py`, `app/schemas/query.py`, `docs/database.md` | `test_query_ownership.py` (8); updated `test_authorization_matrix.py::test_my_queries_only_returns_the_callers_queries`, `test_list_params.py::test_my_queries_is_bounded` | red (victim's query visible after registering their email); green |
| **A3** rate-limit key behind nginx | fixed | `docker-compose.yml`, `Dockerfile`, `frontend/nginx.conf` (comment only: `$proxy_add_x_forwarded_for` was already in place) | `test_deploy_config.py` (6) + live two-container check | live: before = every client shares nginx's bucket (client B throttled at once); after = separate buckets, spoofed XFF ignored |
| **A4** compose exposure | fixed | `docker-compose.yml`, new `docker-compose.dev.yml`, `.env.example`, `docs/setup.md` | `test_deploy_config.py` (4) + `docker compose config` | only the frontend is published; `POSTGRES_PASSWORD` required; dev override binds 127.0.0.1 |
| **A5** public blood-request abuse | fixed | `app/config.py`, `app/services/email_service.py`, `app/api/v1/blood_requests.py`, `app/schemas/blood_request.py`, `frontend/src/pages/GenerateRequests.jsx` | `test_blood_request_abuse.py` (9) | dedicated `5/minute;30/hour`, optional reCAPTCHA, ONE BCC email capped at 20; "after commit" was already true (existing `test_commit_before_response.py`) |
| **A6** bcrypt blocks the event loop | fixed | `app/api/auth/utils.py` (`hash_password_async`, `verify_password_async`), `router.py`, `donors.py`, `admins.py` | `test_password_handling.py` (A6 part, 6) | red (ran on the loop thread); green |
| **B1** config validation everywhere | fixed | `app/config.py`, `tests/conftest.py` (pins `SECRET_KEY`/`APP_ENV`/`RECAPTCHA_ENFORCED`), `.env.example`, `docs/setup.md` | `test_config_validation.py` (18), `test_env_example.py` (+2) | placeholders and keys under 32 chars refused in every env; production needs reCAPTCHA enforced; errors no longer echo secrets |
| **B2** password byte limit | fixed | new `app/schemas/passwords.py`, `schemas/donor.py`, `schemas/admin.py`, `router.py` | `test_password_handling.py` (B2 part) | 72 UTF-8 bytes, clear 422; reset now enforces the registration policy |
| **B3** account enumeration | fixed | `router.py`, `utils.py` (`DUMMY_PASSWORD_HASH`) | `test_password_handling.py` (B3 part) | same 400 for known/unknown on confirm; dummy bcrypt on unknown login; reset email sent after the response |
| **B4** OTP attempt counter | fixed | `app/services/otp_service.py` | `test_otp_window.py` (4) | attempts and window survive a re-request; locked record kept until the window ends |
| **B5** refresh rotation race | fixed | `refresh_session_service.py` (`claim_session`), `router.py` | `test_refresh_race.py` (2) + real-Postgres concurrent check | atomic `UPDATE ... WHERE revoked_at IS NULL` + rowcount |
| **B6** logout / donor logout | fixed | `frontend/src/pages/DonorDashboard.jsx`, `docs/setup.md` | existing `http.test.js` logout tests; backend logout tests already existed | donor **Log out** button; logout still needs no access token; access-token lifetime documented |
| **B7** admin safeguards | fixed | `app/api/v1/admins.py`, `app/schemas/admin.py`, `app/repositories/admin.py` | `test_admin_safeguards.py` (10) | no self-deactivation, no deactivating the last active admin; other admins' DOB/phone hidden |
| **B8** email normalization | fixed | `app/models/donor.py`, migration `0008`, new `app/utils/emails.py`, repositories, `router.py`, `donors.py`, `admins.py` | `test_email_normalization.py` (16), `test_email_migration.py` (6) | lowercase on write and lookup, unique `lower(email)` index, migration refuses and lists case-variant duplicates, admin addresses refused at donor registration |
| **B9** nginx security headers | fixed | `frontend/nginx.conf`, new `frontend/security-headers.conf`, `frontend/Dockerfile` | `test_deploy_config.py` (4) + real `nginx -t` and a live header check | CSP built from the origins the frontend really loads; **not tested in a browser** |
| **B10** `BloodBanks.jsx` href | fixed | new `frontend/src/services/safeUrl.js`, `BloodBanks.jsx` | `frontend/src/services/safeUrl.test.js` (5, incl. a guard that fails on any unchecked `href={...}`) | red on `BloodBanks.jsx:328`; green |
| **B11** health + docs | fixed | `app/api/v1/health.py`, `app/main.py`, `app/config.py` (`DOCS_ENABLED`) | `test_diagnostics.py` (10) | health leak reproduced then fixed; docs off when `APP_ENV=production` |
| **B12** atomic transitions | fixed | `app/repositories/blood_request.py`, `app/api/v1/blood_requests.py` | `test_request_transitions.py` (6) + real-Postgres concurrent check | compare-and-swap in the UPDATE; loser gets 409 before any email or counter |
| **B13** scheduler | fixed | `app/tasks/scheduled_jobs.py`, `app/core/scheduler.py` | `test_age_job.py` (21) + real-Postgres run | ages recomputed from DOB (idempotent, catches up); 29 Feb turns a year older on **1 March**; misfire grace 6 h, coalesce, max 1 instance |
| **B14** certificates | fixed | `app/services/certificate_service.py`, `app/services/email_service.py` | `test_certificate_hardening.py` (16) | `fullmatch` and `[0-9]`; UTF-8 placeholder; email package quotes the filename; 8-hex suffix prevents same-second overwrite |
| **B15** seed-data guard | fixed | new `scripts/load_dev_data.py`, headers of `docs/*.sql`, `docs/setup.md` | `test_load_dev_data.py` (14) | refuses `APP_ENV=production` and any non-empty database |
| **B16** `.dockerignore` | fixed | new `.dockerignore`, `frontend/.dockerignore` | `test_docker_context.py` (39) + real context listings | API context = 88 files, no secrets/dumps/certificates; `docker build --check` clean |
| **B17** pins | fixed (partly yours) | `Dockerfile`, new `requirements-runtime.in/.lock`, `.github/workflows/ci.yml`, new `docs/supply-chain.md` | `test_supply_chain.py` (8) + a real image build + `pip-audit` | uv pinned by version+digest, hashed lock installed with `--require-hashes`. **Actions' SHAs and base-image digests are yours to look up** (commands in `docs/supply-chain.md`) |

## Part C: review findings (written before the fixes; the review was read-only first)

**C1 Public diagnostics and error handlers** (`health.py`, `main.py`, `exceptions.py`)
- DEFECT, fixed (B11): `/health` returned the raw driver error (hostnames, users) to anonymous callers. Reproduced.
- DEFECT, fixed (B11): `/docs`, `/redoc`, `/openapi.json` always on.
- Observed, not changed: the `LifeConnectException` handler returns `details`, which for `DuplicateEntityError` includes the
  submitted value; nothing raises those classes today (latent). `RateLimitExceeded` answers with the limit text.
  FastAPI's default 422 echoes the submitted value back to the sender.

**C2 Build context and image contents**
- DEFECT, fixed (B16): no root `.dockerignore`. The API image copies only `app/`, `alembic.ini` and `migrations/`, so the
  image itself was clean; the context (sent to the daemon) held `.env`, `source_db.sql`, the venv, certificates.
  `frontend/.dockerignore` already excluded `.env`, `node_modules`, `dist` (the audit's claim about `frontend/.env` was
  partly wrong); `.env.*`, `.git`, `.vite`, `coverage` were added.
- Built image inspected: no `.env`, `.sql`, `.dump`, `.pdf`, certificates or tests; runs as uid 1000; no `curl`/`uv`.

**C3 Seed data, bootstrap admin, scripts**
- DEFECT, fixed (B15): the documented bootstrap admin has a published password and nothing stopped it being loaded
  anywhere.
- Reviewed, no defect: `scripts/migrate_legacy_dump.py` (own parser, SQLAlchemy Core with metadata identifiers, refuses
  non-empty targets, no string-built SQL); `scripts/drop_aadhaar_column.py` (two explicit confirmations, constant DDL);
  migrations `0004`-`0006`. `0005` is non-destructive.

**C4 Personal data in responses and mass assignment**
- DEFECT, fixed: donors and anonymous submitters received the replying admin's internal `admin_id` in query responses
  (new `QueryPublicResponse`, admin view unchanged).
- DEFECT, fixed: `PATCH /hospitals/{id}` with an explicit `null` for a required field crashed (`AttributeError`, then a NOT NULL
  violation) and answered 500; now a 422.
- Verified by tests (no defect): no update or create body can set ids, roles, status, counters, ownership, credentials
  or approvers (`test_mass_assignment.py`, 12). `DonorUpdate`/`AdminUpdate`/`HospitalUpdate` persist exactly their fields.
- Fixed under B7: `AdminResponse` exposed every admin's DOB and phone to every other admin.

**C5 SPA nginx edge and npm chain**
- DEFECT, fixed (B9): no security headers on SPA pages.
- `npm audit`: **0 vulnerabilities** (all and production). `pip-audit` on the real image set: 1 advisory, `ecdsa`
  PYSEC-2026-1325 (no fix; unused, HS256 only), ignored in CI with a written reason.

**C6 Scheduler, audit log, mail templates**
- Verified, no defect: every admin write route records an audit row (a test enforces it per route), the actor always
  comes from the authenticated admin object, and no API route reads, edits or deletes the audit table. Every value that
  reaches a mail template is escaped (a test sends script payloads through all four templates).
- Fixed: the age job (B13). Jobs are lock-guarded and idempotent; the age job was not.

## Observed, NOT fixed (needs your decision or is outside the brief)

1. **Donors in the post-donation cooldown cannot log in.** `active_status` is both "may authenticate" and "eligible to be
   emailed", and `update_last_donated` sets it false for `DONOR_ELIGIBILITY_DAYS`. Product decision.
2. **Frontend success checks that never succeed**: `QueryPageDonor.jsx` and `DonorNewPassword.jsx` test `res.success === true`,
   but the API returns the created object or a message. `GenerateRequests.jsx` had the same bug and was fixed because it is the
   form A5 protects (a "failed" success invites resubmission).
3. **The password-reset pages do not carry the email or OTP between steps** (`DonorNewPassword` takes an `email` prop `App.jsx`
   never passes), so the reset flow looks incomplete on the frontend. Backend is fine and tested.
4. `BloodRequestCreate.due_date` accepts dates in the past.
5. `app/core/security.py` is a dead, deprecated duplicate of the password helpers (nothing imports it).
6. `python-jose` pulls in `python-ecdsa` (advisory above); moving to PyJWT would remove it (dependency change, not done).
7. The audit table is append-only by convention, not enforced by the database, and failed logins and password resets are not audited.
8. Admin authorization is still flat apart from B7's two safeguards: any active admin can edit or deactivate any other.

## Contract changes

API (OpenAPI snapshot `tests/contract/openapi_snapshot.json` regenerated and each diff reviewed):
- `POST /blood-requests/` body gains optional `recaptcha_token`; the route is rate limited (`BLOOD_REQUEST_RATE_LIMIT`) and may answer 429/400.
- `GET /admins/{id}` and `PUT /admins/{id}` return `AdminResponse | AdminSummaryResponse`; the summary lacks `date_of_birth` and `mobile_number`. `GET /admins/` items follow the same rule (full record only for the caller's own row).
- `POST /queries/` and `GET /queries/my-queries` return `QueryPublicResponse` (no `admin_id`). **`/queries/my-queries` now lists only queries the donor filed while signed in**; anonymous and pre-existing queries no longer appear there.
- `POST /auth/*/password-reset/confirm`: unknown email now answers `400 Invalid or expired OTP` (was `404`). Reset passwords are validated like registration (8+, upper case, digit, 72 bytes) and `422` is returned otherwise. Login passwords over 72 bytes get `422`.
- `POST /donors/register`: an email that differs only in case, or belongs to an admin, is `409`. Stored emails are lowercase.
- Approve/decline/close answer `409` if the request changed underneath the admin.
- Deactivating yourself is `400`; deactivating the last active admin is `409`.

Environment / config:
- **New required**: `POSTGRES_PASSWORD` (compose, no default). `SECRET_KEY` must be 32+ chars and not a placeholder **in every environment** (the app refuses to start otherwise; this includes your existing `.env` if its key is short).
- New optional: `BLOOD_REQUEST_RATE_LIMIT` (`5/minute;30/hour`), `ADMIN_NOTIFY_MAX_RECIPIENTS` (20), `DOCS_ENABLED`, `FORWARDED_ALLOW_IPS` (compose-level, default the pinned nginx address).
- `APP_ENV=production` now also requires `RECAPTCHA_ENFORCED=true`.

Migrations added: `0007` (nullable `query_table.donor_id` + FK + index), `0008` (unique index on `lower(donor_details.email)`; stops and lists duplicates). Both are reversible and tested on SQLite and Postgres, including an upgrade of a populated 0004-era database.

## Manual steps for you

1. **Replace `SECRET_KEY` in your real `.env` if it is short or a placeholder** (the app and `alembic` will refuse to start): `python -c "import secrets; print(secrets.token_hex(32))"`. Add `POSTGRES_PASSWORD` for compose.
2. Before `alembic upgrade head` on a real database, check for case-variant donor emails (query in `docs/setup.md`). Migration `0008` also stops and lists them.
3. **Pin the GitHub Actions to commit SHAs and the base images to digests**: commands in `docs/supply-chain.md`.
4. **Browser checks I could not do**: the CSP on the login pages (reCAPTCHA), landing page (Font Awesome) and signup page (Google Fonts); the donor Log out button; the blood-request form with reCAPTCHA on.
5. **Deployment checks**: set `APP_ENV=production`, `RECAPTCHA_ENFORCED=true`, `RECAPTCHA_SECRET_KEY`; confirm `/docs` is 404; confirm only port 80 is reachable on the host; put TLS in front (HSTS does nothing over HTTP); if a load balancer sits before nginx, set `FORWARDED_ALLOW_IPS` to the address that actually connects to the API, never `*`.
6. **Credential rotation and history scrub** are unchanged from `docs/HISTORY_SCRUB.md`: `source_db.sql` (real personal data) is still in git history until you run it; rotate anything that was in it.
7. Merge Dependabot's pull requests once digests are pinned, otherwise the pins go stale.
8. Decide the observed items above (cooldown login, the broken frontend success checks, the reset-page flow).

## Verification

Run for real:
- Full backend suite against a throwaway Postgres (501 passed). Postgres migration tests: `upgrade head` on an **empty** database
  (0 tables to 16, `alembic check` clean, full downgrade to base and back up, check clean), and an upgrade of a **populated
  0004-era** database (rows kept, retired Aadhaar values kept, downgrade and re-upgrade lossless).
- A one-off script drove the real app against Postgres with genuinely **concurrent** requests (18/18): two refreshes of one token,
  two approvals, and two closes of the same request each had exactly one winner; the donor was emailed once and the donation
  counted once; the age job ran on Postgres. (Script was in the scratchpad, not added to the repo.)
- An isolated `docker compose` stack with throwaway secrets (built the real images, ran `alembic upgrade head` on an empty Postgres,
  nginx in front): only the frontend port was published; API and Postgres were unreachable from the host; four client containers with
  distinct IPs each got their own rate-limit bucket; a rotating spoofed `X-Forwarded-For` got no extra attempts, through nginx or
  straight at the API; the API logged the real client addresses. Re-run with the old trusted-proxy setting: one client throttled
  everyone (the audited problem). Stack, images, volumes and network were removed afterwards.
- Real nginx: `nginx -t` on the new config and a header check on `/` and an asset path. Real Docker: build-context listings (API 88
  files, frontend 140, no secrets/dumps/certificates), `docker build --check` clean, API image built from the hashed lock and imports
  every runtime package (bcrypt 3.2.2), contains no `.env`/dumps/tests and runs as uid 1000.
- Clean-setup check from a copy of the tree without any `.env`: fresh venv, `pip install -r requirements.txt`, `cp .env.example .env`;
  the app refuses the placeholder `SECRET_KEY` with the documented message, starts with a generated one, and the suite passes without
  reading `.env`.
- Self-review of the diff: no leftover synchronous `hash_password`/`verify_password` calls, no unawaited coroutines (heuristic), every
  module imports cleanly in each entry order (a real circular import found and fixed in `refresh_session_service`), ruff F-class
  checks (undefined names, redefinitions) clean apart from one pre-existing redefinition. One bug found and fixed in review: the age job
  would have written a negative age for a date of birth in the future.

Found and fixed along the way (so the numbers above are trustworthy): my first `test_upgrade_from_0004` asserted exact table counts, so
rows left in the shared throwaway database by my own smoke script made it fail. It now asserts only on the rows it seeds, and was
checked with a stray row present. One full run (the third) took 29 minutes and reported 1 failure in that same Postgres test while
the machine's clock jumped about 30 minutes; I did not capture its error and it did not recur in two further full runs (501 passed
each time), so I treat it as a stall in my environment, not a code defect, but I cannot prove that.

NOT run / not possible here:
- **Anything in a real browser**: the CSP on the login (reCAPTCHA), landing (Font Awesome) and signup (Google Fonts) pages; the donor
  Log out button; the blood-request form with reCAPTCHA enforced. The frontend only had lint, build and node tests.
- **GitHub Actions**: `ci.yml` was edited (audit step) but not run. The `pip-audit` commands in it were run by hand in a container.
- **Python 3.11**: the suite ran on Python 3.14 (the only interpreter on this machine; the project targets 3.11). The API image, which
  uses 3.11, was built and its imports checked, but the test suite was not run inside it.
- **TLS/HSTS** and **real SMTP**: neither exists locally; mail was captured with a spy.
- `mypy`, and the project's own ruff style rules (pre-existing noise); only the bug-finding checks were run.
- The `lc-test-pg` throwaway container is removed at the end of the session. `lc-migrate-pg` was already there and was not touched.

## Follow-up pass: C1 error details and P2-43 production guard

Two items previously left as "observed" / configurable-only are now enforced in code.

- **C1 (error responses):** `LifeConnectException.details` is no longer returned to clients. The handler
  (`app/main.py:lifeconnect_exception_handler`) returns `{detail, error_id}` in every environment and adds
  `error_details` only when `DEBUG=true` **and** `APP_ENV` is `development`/`test`; details are logged at
  debug level under the same `error_id`. Covered by `tests/test_error_responses.py` (3 tests).
- **P2-43 (rate limiter):** `APP_ENV=production` now refuses to start with `RATE_LIMIT_STORAGE_URI` empty or
  `memory://…`; a shared store (e.g. `redis://redis:6379/0`) is required so the worker/replica count cannot
  multiply the effective limit. Covered by `tests/test_rate_limit_config.py` (4 new cases). `.env.example`
  and `docs/setup.md` updated.

Still open from the same review: FastAPI's default 422 body echoes the submitted `input` (including a
password on validation failure), so a custom `RequestValidationError` handler is the remaining half of the
error-response fix. Backend suite after this pass: 502 passed, 9 skipped (SQLite; the skips are Postgres-only
and one Windows-only filename test).


## Phase 1 Task 1: exposure containment preparation

- Removed personal identifiers from the history-cleanup guide and replaced the procedure with an owner-controlled incident, credential rotation, session revocation, verification and coordinated rewrite checklist. Historical objects and the ignored local dump still contain sensitive data. No history rewrite, credential rotation, production revocation or remote operation was performed.
- Expanded Git and Docker exclusions for nested environment files, databases, backups and key stores; retained explicit tracked synthetic SQL fixtures. Added Docker-context regression cases.
- Added a redacted full-history and working-tree Gitleaks CI job. The job is not locally verified because Docker is unavailable; existing historical findings may block it and require owner-led remediation, not an allowlist.
- Local detect-secrets 1.5.0 scan of tracked files (excluding lockfiles) returned candidate findings requiring review. The attempted history patch scan was inconclusive; no clean-history claim is made. See PHASE_1_COMPLETION_REPORT.md for limitations and baseline results.
- Full backend rerun with a writable workspace temporary directory: 518 passed, 9 skipped; frontend: 31 tests passed, lint passed, build passed. Ruff baseline has 702 findings.

## Phase 1 Task 2 — Donor password reset

- The donor pages now send one confirmation with the email, code and new password. Reset state lives in memory while the donor moves through the existing screens. Direct visits and page reloads restart the flow.
- The backend now saves OTP consumption, the new password and session revocation in the same transaction. Donor reset validation errors omit submitted values.
- Added backend and frontend regressions and an opt-in Edge/Chromium test of the built application with synthetic mail. The focused backend suite passed 39 tests. Frontend unit tests (32), ESLint, the production build and the browser test passed.
- Full backend suite with a writable temporary directory: 523 passed, 9 skipped.

## Phase 1 Task 3 — Administrator password reset

- Administrator reset now submits the registered email, OTP and new password through the existing confirmation endpoint. Donor and administrator reset state use separate route groups and stay in memory.
- Successful confirmation saves OTP consumption, the password update and session revocation together. Tests cover role separation at the same email, privilege preservation, expiry, replay, generic errors and preservation of an OTP after a failed update.
- Administrator reset validation errors omit submitted fields. Added an API regression and extended the opt-in browser check to exercise both role flows.
- Verification passed with 530 backend tests (9 skipped), 33 frontend tests, ESLint, the production build and two Edge end-to-end tests.

## Phase 1 Task 4 - Production HTTPS and deployment

- Added the production Compose overlay with a configurable hostname and reCAPTCHA site key, read-only TLS mount, private PostgreSQL and Redis, and production application defaults. The base file keeps local HTTP on loopback.
- Nginx now redirects to the configured HTTPS hostname, enables TLS 1.2 and 1.3, sets HSTS on HTTPS responses, replaces untrusted forwarding metadata and permits reCAPTCHA connections in CSP. FastAPI validates production CORS and debug settings.
- Added deployment tests and certificate installation and renewal instructions. Compose models and native Nginx TLS checks passed. Docker Desktop returned HTTP 500 before it could build either image.
- Corrected three UTC-sensitive request test fixtures without changing their assertions. The final backend suite finished with 541 passed and 9 skipped. Frontend checks and both Edge password reset tests passed.

## Phase 1 Task 5 - CI security scans

- Retrieved the original container job log. Setup could not resolve the legacy Trivy action tag, so neither the image build nor scan ran.
- Added independent API and frontend scans with SHA-256-verified scanner binaries, full action commit pins, read-only repository permissions, and audits for Python runtime, Redis and all npm dependencies. Both package audits reported no known findings.
- Registry-base scans found high-severity packages in Python, Nginx and Node. Dockerfiles now upgrade Alpine packages, omit unused Python packaging tools from the runtime and use a patched npm version. Final image scans remain blocked by the unavailable Docker Linux engine.
- Repaired the Python project dependency table and regenerated `uv.lock`. The frontend lockfile installed successfully with npm 12.2.3. Current and local-history Gitleaks scans passed after reviewing four exact historical false positives. Historical personal data still requires the owner's cleanup.

## Phase 1 Task 6 - Donor data erasure

- Added password-confirmed donor submissions, super administrator review, transactional removal of linked records and sessions, and a retry queue for identified certificate files. Donation unit totals and unrelated records are preserved.
- Added migration `0012`, the privacy screens, API authorization and regression tests, and a browser test. Drafted the privacy notice, retention and backup procedures for owner approval.
- Final verification: 560 backend tests passed with PostgreSQL cases enabled, 1 skipped. The frontend passed 33 tests, ESLint and production build. Three Edge regressions, the focused migration suite and a donor erasure API check against PostgreSQL passed.
