# Phase 2 security hardening

**Overall verdict: PARTIAL.** All ten tasks received application changes or regression coverage on `fix/phase-2-security`. Local tests cover donor enrollment and recovery, administrator privileges, blood requests, certificate delivery and shared rate limits. Production acceptance remains open for the deployed proxy and integrations, container checks and the Phase 1 incident involving sensitive Git history. This branch requires no database migration.

## Baseline and scope

The branch starts at cf74a9c, the development tip verified with `git ls-remote origin refs/heads/development`. The initial remote lookup was blocked by the sandbox and the approved read-only retry succeeded. The pre-existing untracked .claude directory was preserved. No commits, pushes, deployments, credential rotations or production operations were performed.

The React/Vite client uses in-memory bearer access tokens. FastAPI validates HS256 signatures, expiry, token type, active account and token version. SQLAlchemy persists accounts, purpose-bound OTPs and refresh sessions in PostgreSQL. The refresh cookie is HttpOnly and SameSite=Strict. HTTPS environments use a Secure, host-bound cookie with Path=/ and development uses an auth-path cookie. Nginx fronts the deployment. Single-session logout revokes the refresh chain. Its issued access token can remain valid until expiry (15 minutes by default). Logout-all and password reset invalidate earlier bearer tokens.

## Findings and remediation

| Task | Severity | Finding and impact | Implemented control |
| --- | --- | --- | --- |
| 1 | High, conditional on concurrent legacy login | A login-time administrator scrypt upgrade could overwrite a concurrent reset with the old password hash. | Lock the administrator row across login, reset and refresh. A PostgreSQL test checks the lock during migration. Existing reset tests check old/new credential behavior. New passwords use bcrypt cost 12. |
| 1 | High if seeded accounts are reachable | Development SQL supplied an administrator login with a publicly documented password. | Both SQL fixtures now contain unusable password markers. The guarded loader can hash an operator-supplied DEV_SEED_PASSWORD for local login. Production and populated-database guards remain. |
| 1 | Medium | Public donor registration disclosed address availability and allowed registration without mailbox access. | The code-request endpoint takes only an email and performs the same dispatch for new, donor and administrator addresses. The registration endpoint verifies an email- and purpose-bound code before any membership lookup. Successful account creation consumes it transactionally. A mailbox owner can still receive a conflict and use recovery. |
| 1 | Medium | Concurrent logout could miss the successor of a refresh token. | Lock and reread each refresh row before following its successor. A two-transaction PostgreSQL regression checks the successor is revoked. |
| 1 | Medium, configuration dependent | OTPs could be configured with excessive lifetime or attempt budget. | Startup bounds are 1–900 seconds and 1–10 attempts. Defaults are 600 seconds and five attempts per active window. Reset codes use a cryptographic RNG, keyed HMAC, purpose binding and transactional consumption. |
| 1 | Low | Refresh replay cookie deletion was lost during exception handling. Failed administrator signup could prematurely consume an invitation. Auth validation errors could echo submitted fields. | Attach deletion headers to refresh exceptions, consume invitations with account creation, and return validation locations, messages and types on credential-bearing routes. |
| 2 | High, conditional on possession of an existing session | An ordinary administrator session could inherit super-admin rights after promotion. | Actual role changes increment the account token version and revoke refresh sessions. Privilege checks use the current database role. |
| 2 | Medium | Concurrent role or status changes could defeat the last-super-admin check or use stale management authority. | Lock actor, target and active super administrators in stable ID order, refresh account state and recheck the actor. PostgreSQL regression checks simultaneous self-demotions leave one active super administrator. |
| 2 | Medium | A donor bearer token could regain access after donor deactivation and reactivation. | Actual donor status transitions atomically increment the token version. Regression checks the original bearer and refresh credentials fail and fresh login succeeds. |
| 2 | Low | Logout-all also revoked a refresh chain supplied by cookie even if it belonged to another account. | Limit server-side revocation to the authenticated account and clear the browser cookie. Mixed-account regression checks the other account retains its session. |

## Permissions reviewed

The OpenAPI contract contains 67 operations. The authorization matrix exercises 47 bearer-protected operations and maintains an explicit allowlist of 20 operations without a bearer requirement. Some of the latter require an OTP or a refresh cookie.

| Principal | Permitted operations |
| --- | --- |
| Public visitor | Read API health/info and public hospital directory, submit blood requests or support queries, request enrollment/recovery, and authenticate. Account creation requires an enrollment or invitation code. |
| Donor | Read and edit permitted fields on own profile, see own authenticated queries, request and view own erasure, revoke own sessions. Server-side ownership uses authenticated account IDs. |
| Administrator | Operate donor, hospital, blood-request, query, certificate and analytics workflows. Read administrative summaries, read own private profile, edit own name and phone. |
| Super administrator | Administrator capabilities plus invitations, account activation/deactivation and role management, and erasure review. Last-active-super-admin and self-deactivation safeguards apply. |

Authorization and mass-assignment regressions exercise missing, invalid, expired, refresh-as-access and inactive tokens, cross-role requests, cross-donor reads/writes, administrator privilege changes and submitted privileged fields. Blood-request transitions retain their administrator checks. Anonymous query history stays private after a later verified enrollment with the same email.

## Compatibility and deployment actions

- Deploy the enrollment frontend and API together. Other clients must call POST /api/v1/donors/register/code with email, then include enrollment_code with the usual registration body. Successful registration still returns HTTP 201 and the donor profile.
- Configure working SMTP for new enrollment. The browser checks used a synthetic mailbox. Real mail delivery, the deployed TLS/proxy and Redis configuration, and staging reCAPTCHA remain unverified. Task 6 verified HTTPS cookies through a local Nginx proxy.
- Existing donors can continue to sign in. The change verifies new registrations only. If old development seeds ever reached a shared environment, identify affected accounts and arrange password resets and session revocation. Seed changes cannot remediate existing rows.
- Phase 1 acceptance remains open for sensitive Git history and credential incident response, final container builds and scans, staging configuration and privacy/retention approvals. Follow docs/HISTORY_SCRUB.md with the appropriate owner authorization.
- Task 5 declared the already installed limits 5.8.0 as a direct dependency. Package consistency passed. See Task 9 for the final dependency audits.

## Task outcomes

| Task | Outcome |
| --- | --- |
| 1 Authentication | PASS for the locally verified application flows |
| 2 Authorization | PASS for the reviewed server routes and local regression matrix |
| 3 API security | PASS for local API and workflow verification |
| 4 Input validation and output safety | PASS for the local application and tested rendering paths |
| 5 Rate limiting | PASS. Local enforcement, recovery and counter sharing between two limiter instances passed against disposable Redis 7.4.11. |
| 6 CORS, CSRF and session security | PASS for local HTTPS and application verification |
| 7 File security | PASS for locally verified certificate workflows. User uploads are not applicable. |
| 8 Headers and errors | PASS for FastAPI and the local HTTPS proxy |
| 9 Configuration and dependencies | PASS for source configuration, package consistency and advisory checks. Owner-led incident response remains open. |
| 10 Full-phase regression | PARTIAL. Local application regressions passed. Container image and staging checks remain unverified. |

## Earlier verification checkpoints

- Earlier Task 1 checkpoint: 99 focused backend cases, 31 PostgreSQL workflow cases and three refresh-race cases passed in overlapping runs.
- `npm.cmd test` in frontend passed all 33 tests. `npm.cmd run lint` and `npm.cmd run build` passed. Vite reported its existing bundle-size warning.
- `venv/Scripts/python.exe -m pytest -q tests/browser_enrollment.py tests/browser_donor_reset.py tests/browser_erasure.py` passed four Edge browser journeys against built assets, real FastAPI handlers, isolated data and synthetic mail. Enrollment covered incorrect code, corrected submission and the confirmation page.
- `pytest -q tests/test_legacy_hash.py tests/test_admin_roles.py tests/test_admin_safeguards.py tests/test_refresh_race.py tests/test_enrollment.py tests/test_session_revocation.py` passed 37 tests with LC_AUTH_TEST_POSTGRES_URL set to a disposable loopback PostgreSQL 18 cluster. Three tests used independent PostgreSQL transactions. The other cases used the standard isolated SQLite fixtures.
- `pytest -q tests/test_seed_data.py tests/test_load_dev_data.py` passed 19 cases. `pytest -q tests/test_session_revocation.py tests/test_admin_safeguards.py tests/test_config_validation.py tests/test_enrollment.py tests/test_api_contract.py` passed 42 cases. The OpenAPI snapshot was deliberately updated for the new operation and registration field.
- The first full run overlapped edits and returned 558 passes, 10 skips and two failures. It collected the superseded published-seed assertion and inspected an administrator route after its source lines had changed. The suite was restarted after those source and test edits. The newly extended erasure test was also run separately.
- `venv/Scripts/ruff.exe check app scripts tests --select E9,F63,F7,F82` and `git diff --check` passed. Repository deprecation and local pytest cache warnings were visible.

- All 132 cases in twelve API modules passed directly on disposable PostgreSQL 18. The temporary copy of the standard pytest fixture substituted PostgreSQL for SQLite. The modules were test_authorization_matrix, test_admin_roles, test_admin_safeguards, test_mass_assignment, test_query_ownership, test_enrollment, test_session_revocation, test_legacy_hash, test_refresh_race, test_admin_password_reset, test_donor_password_reset and test_blood_requests. The command was `pytest -q -c pyproject.toml --confcutdir=<temporary-suite> <temporary-suite>`.
- `pytest -q tests/test_erasure.py` passed four tests. Approved erasure now deletes donor enrollment and reset codes while retaining independent administrator recovery records.

- `pytest -q tests/test_email_migration.py tests/test_migrations.py tests/test_upgrade_from_0004.py tests/test_scheduler.py -k 'postgres or second_instance'` passed all eight selected cases using a newly created, empty database in the disposable cluster. The server was stopped afterward.

- Final default backend run, `venv/Scripts/python.exe -m pytest -q -rs --basetemp=<fresh-workspace-directory>`, completed with **561 passed, 12 skipped, 118 warnings**. Eleven skips passed in the separate PostgreSQL runs above. The certificate filename case requires a filesystem that accepts characters Windows prohibits and was skipped at this Windows checkpoint. The separate erasure run covered its final enrollment-code change. Counts across commands overlap.

## Task 3 API security

The route inventory below covers every application operation under /api/v1. It was checked against the OpenAPI contract, endpoint dependencies, request schemas, repository queries and rate-limit declarations. All 47 bearer-protected operations remain protected. Twenty operations accept requests without bearer authentication, with OTP, password, refresh cookie or reCAPTCHA requirements where indicated.

| Initial finding | Severity | Remediation and evidence |
| --- | --- | --- |
| The default limiter did not find nested FastAPI routes. Varying object IDs could also create separate URL-based buckets. | Medium | Apply the configured default using FastAPI's resolved endpoint and caller IP. Explicit route decorators retain their own policies. A test uses three distinct hospital IDs and observes 404, 404, 429, then a successful call to another operation. |
| JSON bodies could reach the parser without an application size limit. Validation errors on several APIs included submitted values. | Medium | The ASGI boundary counts actual bytes including streamed chunks. It rejects bodies over 64 KiB, ambiguous framing/authentication headers, unsupported encodings and invalid JSON. Error responses omit input values and validation context. |
| Listings accepted excessive offsets, unknown filters and in one public autofill route a negative SQL limit. Several collections had no page controls. | Medium | Bound pagination, ID and search inputs. Reject unknown/repeated scalar parameters. Paginate public cities, the blood-group lookup and certificate listings. Internal donor notifications keep their own eligibility query. |
| The certificate email operation accepted a recipient independently of the certificate's owner. | Medium | Match the recipient against the generation audit record before queuing mail. The regression checks rejection for another donor, no mail sent on rejection, and successful delivery to the correct donor. Legacy files without a generation record require regeneration for email delivery. |
| Several request models silently discarded extra fields, including privileged or obsolete inputs. | Low | Reject unexpected fields on request models, including nested donor details. Regressions check rejection plus valid, authorized updates. The blood-request and query-reply clients send declared fields. |

At the application boundary, an oversized body returns 413, an excessive URI returns 414, unsupported body media types return 415, and excessive headers return 431. Malformed JSON or ambiguous framing returns 400. Invalid schema and parameter values return 422. Normal routing and account/owner checks continue to produce method, authentication and permission errors. New code or schemas introduce no raw SQL from clients. The reviewed repositories use SQLAlchemy expressions with bound values, and wildcard searches escape user input. The raw SQL found in the running application was a constant health check and a parameterized scheduler lock. Existing response models limit sensitive fields, and internal errors use a correlation ID.

**Compatibility and limitations.** Callers must send declared JSON fields and query parameters. The browser selects a hospital from the bounded autofill endpoint and submits its ID. List clients can advance using the documented pagination parameters. The certificate list still scans and sorts its directory to calculate an exact visible total. Its HTTP page is bounded, and its filesystem work scales with the stored collection. Service-wide timeouts and production ingress behavior remain deployment checks. Account-based throttling and trusted proxy verification remain in Task 5. File storage review continues in Task 7.

**Task 3 verification.** PostgreSQL 18 ran in a fresh disposable loopback database and was stopped afterward. The API-limit, authorization-matrix, pagination, mass-assignment, certificate, search-escaping, blood-request and rate-limit modules passed all 118 cases using PostgreSQL-backed fixtures (`pytest -q -c pyproject.toml --confcutdir=<temporary-suite> <temporary-suite>`). A focused backend run covering API boundaries, erasure, authentication, authorization and throttling passed 122 tests. These runs overlap.

The initial full backend run returned 568 passes, 12 skips and one failure. The erasure test still expected success for a body that supplied an unauthorized donor_id. It now checks HTTP 422, retries with the legitimate body and retains the ownership assertions. Browser execution initially failed to load test settings when launched from frontend/. Rerunning from the repository root passed five Edge journeys, including donor submission through hospital autofill and confirmation in the database. The other four covered enrollment, both password resets and erasure. No live mail or production endpoint was used.

**Final results.** The full backend rerun (`venv/Scripts/python.exe -m pytest -q -rs --basetemp=<fresh-directory>`) finished with **572 passed, 12 skipped, 118 warnings**. Eleven skips require optional PostgreSQL fixtures and one requires filename semantics unavailable on Windows. The 118 PostgreSQL Task 3 cases above were run independently. A subsequent focused run of `tests/test_api_limits.py tests/test_certificates.py` passed all 20 cases, including the added city, donor and certificate pagination checks and normalized blood-group filtering. The certificate pagination fixture initially lacked its test output directory and passed after that fixture was corrected. Counts overlap.

The browser command was `pytest -q tests/browser_api_security.py tests/browser_donor_reset.py tests/browser_enrollment.py tests/browser_erasure.py` with the local Edge executable. In frontend/, `npm.cmd test` passed 33 tests, ESLint passed, and the Vite production build passed with the existing bundle-size warning. The fatal Ruff gate and `git diff --check` passed. The rate-limit dependency uses the pinned SlowAPI implementation; retain the nested-route regression when upgrading FastAPI or SlowAPI. Redis-backed multi-instance behavior and production traffic were not exercised.

### Per-operation inventory

Paths below are relative to /api/v1. A bearer token must identify an active account with the current token version. The inputs column names the request model and scalar query keys. Braced path components identify validated path parameters. The OpenAPI snapshot lists response models and success codes. Limits apply per resolved endpoint. The default is 60/minute per IP. Login is 5/minute per IP plus 10/10 minutes per account, Code is 3/minute per IP plus 3/10 minutes per recipient, Support and Blood are each 5/minute plus 30/hour per IP. All values are configurable. See Task 5 for address handling and shared storage.

| Method and path | Access requirement | Request model and query parameters | Rate |
| --- | --- | --- | --- |
| `DELETE /certificates/{filename}` | Admin | None | Default |
| `DELETE /hospitals/{hospital_id}` | Admin | None | Default |
| `DELETE /queries/{query_id}` | Admin | None | Default |
| `GET /` | Public | None | Default |
| `GET /admins/` | Admin | `active_only`, `page`, `page_size` | Default |
| `GET /admins/me/profile` | Admin | None | Default |
| `GET /admins/{admin_id}` | Admin | None | Default |
| `GET /admins/{admin_id}/stats` | Admin | None | Default |
| `GET /analytics/dashboard` | Admin | None | Default |
| `GET /analytics/donors/by-blood-group` | Admin | None | Default |
| `GET /analytics/donors/by-city` | Admin | None | Default |
| `GET /analytics/requests/monthly` | Admin | None | Default |
| `GET /blood-requests/closed` | Admin | `limit`, `offset` | Default |
| `GET /blood-requests/declined` | Admin | `limit`, `offset` | Default |
| `GET /blood-requests/expired` | Admin | `limit`, `offset` | Default |
| `GET /blood-requests/ongoing` | Admin | `page`, `page_size` | Default |
| `GET /blood-requests/pending` | Admin | `page`, `page_size` | Default |
| `GET /blood-requests/stats/summary` | Admin | None | Default |
| `GET /blood-requests/{request_id}` | Admin | None | Default |
| `GET /certificates/` | Admin | `limit`, `offset` | Default |
| `GET /certificates/download/{filename}` | Admin | None | Default |
| `GET /donors/` | Admin | `active_only`, `blood_group`, `name_search`, `page`, `page_size`, `search` | Default |
| `GET /donors/blood-group/{blood_group}` | Admin | `active_only`, `limit`, `offset` | Default |
| `GET /donors/{donor_id}` | Own donor or admin | None | Default |
| `GET /health` | Public | None | Default |
| `GET /hospitals/` | Public | `city`, `page`, `page_size`, `search` | Default |
| `GET /hospitals/autofill` | Public | `limit`, `q` | Default |
| `GET /hospitals/blood-banks` | Public | `city`, `page`, `page_size`, `search` | Default |
| `GET /hospitals/cities` | Public | `limit`, `offset` | Default |
| `GET /hospitals/{hospital_id}` | Public | None | Default |
| `GET /privacy/erasure-requests` | Super admin | `limit`, `offset` | Default |
| `GET /privacy/erasure-requests/mine` | Own donor | None | Default |
| `GET /queries/` | Admin | `page`, `page_size`, `status`, `status_filter` | Default |
| `GET /queries/my-queries` | Own authenticated queries | `limit`, `offset` | Default |
| `GET /queries/pending` | Admin | `limit`, `offset` | Default |
| `GET /queries/{query_id}` | Admin | None | Default |
| `PATCH /admins/{admin_id}/activate` | Super admin | None | Default |
| `PATCH /admins/{admin_id}/deactivate` | Super admin | None | Default |
| `PATCH /donors/{donor_id}` | Own donor | `DonorUpdate` | Default |
| `PATCH /hospitals/{hospital_id}` | Admin | `HospitalUpdate` | Default |
| `PATCH /privacy/erasure-requests/{request_id}` | Super admin | `ErasureDecision` | Default |
| `POST /admins/invite` | Super admin | `AdminInviteRequest` | Code |
| `POST /admins/register` | Admin invitation OTP | `AdminCreate` | Login |
| `POST /auth/admin/login` | Account credentials and configured reCAPTCHA | `LoginRequest` | Login |
| `POST /auth/admin/password-reset/confirm` | Account recovery OTP | `PasswordResetConfirm` | Login |
| `POST /auth/admin/password-reset/request` | Public | `PasswordResetRequest` | Code |
| `POST /auth/donor/login` | Account credentials and configured reCAPTCHA | `LoginRequest` | Login |
| `POST /auth/donor/password-reset/confirm` | Account recovery OTP | `PasswordResetConfirm` | Login |
| `POST /auth/donor/password-reset/request` | Public | `PasswordResetRequest` | Code |
| `POST /auth/logout` | Presented refresh cookie, idempotent | None | Default |
| `POST /auth/logout-all` | Own authenticated account | None | Default |
| `POST /auth/refresh` | Live refresh cookie | None | Default |
| `POST /blood-requests/` | Public and configured reCAPTCHA | `BloodRequestCreate` | Blood |
| `POST /blood-requests/{request_id}/approve` | Admin | `send_emails` | Default |
| `POST /blood-requests/{request_id}/close` | Admin | `BloodRequestClose` | Default |
| `POST /blood-requests/{request_id}/decline` | Admin | `reason` | Default |
| `POST /certificates/generate` | Admin | `CertificateRequest` | Default |
| `POST /certificates/send-email` | Admin, matching generation record | `donor_id`, `filename` | Default |
| `POST /donors/register` | Email enrollment OTP | `DonorEnrollment` | Login |
| `POST /donors/register/code` | Public | `EnrollmentCodeRequest` | Code |
| `POST /donors/{donor_id}/activate` | Admin | None | Default |
| `POST /donors/{donor_id}/deactivate` | Admin | None | Default |
| `POST /hospitals/` | Admin | `HospitalCreate` | Default |
| `POST /privacy/erasure-requests` | Own donor and current password | `ErasureSubmission` | Login |
| `POST /queries/` | Public, optional donor identity | `QueryCreate` | Support |
| `POST /queries/{query_id}/reply` | Admin | `QueryReply` | Default |
| `PUT /admins/{admin_id}` | Admin own allowed fields or super admin | `AdminUpdate` | Default |

## Task 4 input validation and output safety

| Severity | Original finding | Remediation and evidence |
| --- | --- | --- |
| Medium | Inconsistent phone, text and date rules let malformed input reach business logic. Contact information is used to coordinate blood requests. | Shared Pydantic types validate donor, administrator, hospital, blood-request, query and certificate inputs. API tests check rejection before lookup, normalization and field-level errors without echoing submitted values. |
| Low | Some forms assumed a FastAPI validation error was a string. Structured errors could break rendering or obscure why a request failed. | The forms extract text messages with a safe fallback. Signup, query and hospital forms recognize the corresponding successful creation responses. Frontend tests exercise both error shapes. |
| Defense in depth | Nested JSON could contain keys associated with unsafe JavaScript object merging. No exploitable merge was established. | The request parser rejects these reserved keys at every level. Three parameterized tests cover nested keys. |

Names retain Unicode and punctuation, postal codes retain leading zeros, and passwords retain significant spaces. Calendar fields reject numeric timestamps, birth dates reject future values, and blood groups use the eight supported values. Telephone numbers accept common formatting subject to each storage column's limit. The certificate's human-readable donation date remains bounded display text. Existing database rows require no rewrite.

The rendering review covered React text interpolation, dynamic links, HTML email escaping and certificate text drawing. No rich-text editor or raw HTML renderer for submitted query text was identified. An Edge regression stored inert markup through the public query API and verified its exact visible text in the administrator table, with no element created from the markup.

### Task 4 verification

- The default backend suite (`python -m pytest -q -rs`) completed with **592 passed, 12 skipped, 118 warnings**. Eleven skips require opt-in PostgreSQL fixtures and one requires filename semantics unavailable on Windows. Four additional domain cases were added after suite collection and passed in the focused run below. Counts overlap.
- `venv/Scripts/python -m pytest -q tests/test_domain_validation.py -p no:cacheprovider` passed all 22 cases, including malformed and valid phone numbers, postal codes, OTPs, Unicode, dates, blood groups, record IDs, reserved keys and credential preservation.
- `pytest -q tests/browser_output_safety.py tests/browser_api_security.py tests/browser_donor_reset.py tests/browser_enrollment.py tests/browser_erasure.py` passed all six local Edge journeys with built frontend assets, isolated API data and mock mail.
- In frontend, `npm.cmd test` passed 34 tests. `npm.cmd run lint` and `npm.cmd run build` passed. Vite retained its bundle-size warning.
- `venv/Scripts/python -m ruff check --select E9,F63,F7,F82 app tests` and `git diff --check` passed. Pytest reported dependency deprecations and a cache-directory warning during browser testing.
- Live SMTP rendering, production data and the deployed reverse proxy were outside this local verification.

## Task 5 rate limiting and brute-force protection

| Original finding | Severity and impact | Implementation |
| --- | --- | --- |
| Login and code dispatch relied on caller IP. | Medium. Attempts and email deliveries to one address could accumulate across clients. | A second counter uses a domain-separated HMAC of the canonical email and a separate budget per operation. Existing and unknown addresses consume the same budget before lookup, password verification or mail delivery. Both counters use the same configured storage backend. |
| Donor signup, admin invitations and public support submissions inherited the general API quota. Explicit route limits ran after dependency and model checks. | Medium. Higher request volumes could reach verification, support queues or database-backed dependencies. | Added dedicated policies and applied per-IP limits at router dependency entry, including schema-invalid submissions. The SlowAPI decorator observes the completed check. Transport-level rejections in the outer body guard still precede routing. |
| IPv6 address changes within a client network produced new IP buckets. The two IP representations of an IPv4 peer could count separately. | Low. Per-IP quotas were inconsistent across address representations. | IPv6 uses a /64 bucket and mapped IPv4 uses its native IPv4 bucket. Client identity comes from the ASGI peer, with Uvicorn trusting the pinned Nginx address. |
| Quota responses lacked retry timing, and malformed rate policy settings could leave route policy selection to library fallback. | Low. Clients could retry prematurely and operators could miss invalid configuration. | IP and account limits report Retry-After in seconds. Declared policy strings are checked at startup. |

Login, reset confirmation, admin and donor enrollment, invitation, recovery and enrollment email, and donor erasure password reauthentication now have IP and account budgets. Public blood requests and support queries use per-IP limits. Existing database OTP attempt ceilings and single-use verification remain in force. Refresh and logout retain their existing per-IP route limits. Published defaults are in .env.example and docs/setup.md.

### Task 5 verification

- Final full backend run, `venv/Scripts/python -m pytest -q -rs -p no:cacheprovider --basetemp=<fresh-writable-directory>`, finished with **613 passed, 13 skipped, 120 warnings**. Eleven skips require PostgreSQL fixtures, one requires Redis and one requires filename semantics unavailable on Windows.
- An intermediate full run caught a mismatch between requirements.txt and project metadata for the existing limits 5.8.0 dependency. After synchronizing pyproject.toml and uv.lock, `uv lock --check --offline` passed and the combined supply-chain and account test run passed 22 cases with one Redis skip. An earlier run using pytest's default temporary directory encountered Windows access errors. The final run uses a fresh writable base directory.
- `pytest -q -rs -p no:cacheprovider tests/test_account_rate_limits.py` passed 16 tests. One two-worker Redis test skipped. Cases cover accounts across IPs, email case variants, existing and unknown accounts, expiry and valid login after recovery, email suppression, malformed submissions, verification, equivalent IPs and invalid configuration.
- The focused run of account, enrollment, authorization matrix, proxy/deployment, limiter configuration and blood-request abuse tests passed 104 cases with one Redis skip. Counts overlap. Initial checks surfaced enrollment, erasure and role-matrix tests that combined independent security scenarios behind one IP. Those tests now use separate simulated callers or separate scenarios with the original authorization assertions.
- Six local Edge workflows passed using `pytest -q tests/browser_api_security.py tests/browser_donor_reset.py tests/browser_enrollment.py tests/browser_erasure.py tests/browser_output_safety.py`. The tests use real handlers, isolated data and synthetic mail. In frontend, `npm.cmd test` passed 34 tests, and lint and build passed with the existing Vite bundle-size warning.
- `python -m pip check`, the fatal Ruff checks and `git diff --check` passed. No production traffic or infrastructure changes were involved.
- The production Compose overlay selects private Redis and the container installs requirements-redis.txt. The Windows test host lacks a reachable Docker daemon and WSL reports virtualization unavailable. The backend CI job now provisions a disposable redis:7.4-alpine service and installs the pinned Redis driver for this test. Its YAML service, test URL and installation step were checked locally. The workflow has not been run on GitHub. The later full regression run verified counter sharing on disposable Redis. On a host with the optional Redis client, set LC_RATE_TEST_REDIS_URL to a disposable Redis database and run the two-worker test in tests/test_account_rate_limits.py. It uses a unique expiring key.
- Shared networks can exhaust an IP quota, and repeated attempts against one address can temporarily delay its owner. The finite windows allow recovery. Confirm appropriate thresholds with representative traffic before rollout. Phase 2 production readiness remains partial.

## Tasks 6 and 7 findings and remediation

| Task | Severity | Finding and impact | Implementation and evidence |
| --- | --- | --- | --- |
| 6 | Medium | A same-site sibling origin could submit a simple request that caused a refresh or logout. CORS controls what the browser can read, and SameSite=Strict still permits same-site cookies. | The auth router checks a supplied Origin against the request origin and explicit trusted origins. Cookie-bearing refresh and logout without Origin require application/json. Tests confirm untrusted, duplicate and opaque origins fail before cookie rotation or revocation. A second HTTPS origin in Edge could not log out the original session. |
| 6 | Medium, requires control of a sibling domain | A plain production cookie name could collide with a domain cookie created on a sibling. | HTTPS environments use the browser-enforced __Host- prefix, Secure, Path=/ and no Domain. A signed value submitted only under the legacy cookie name fails. Edge confirmed HttpOnly, SameSite=Strict, rotation, new login and logout. Bearer authorization remains required for protected resources. |
| 6 | Low | Credentialed CORS granted any request header and method to allowed origins. The proxy also omitted the external port from the host sent to the API. | Allowlist browser API methods, Authorization and Content-Type. Expose Retry-After and Content-Disposition. Reject wildcard and null origins. Preserve the incoming authority on Nginx so non-default port deployments pass legitimate origin checks. |
| 7 | Medium, requires write access to certificate storage | Resolving a filename before reopening it could follow another directory entry, and in-directory aliases could identify a different certificate for read or deletion. Delivery had no bounded read. | HTTP and SMTP use the same descriptor-checked read, reject non-regular files, reparse points and multiply linked files, and enforce an 8 MiB limit. PNG dimensions and structure, or UTF-8 text, are checked. HTTP sends the verified bytes. Tests cover alternate links, malformed files, size limits and correct PNG/text responses. |
| 7 | Low | Generated names contained donor names. Saves could overwrite a collision or expose unfinished output. Retention scanned unrelated files in the storage directory. | Generate opaque names, write a private temporary file and publish it using an exclusive hard link. A collision leaves the existing file intact. Historical generated names remain valid. Retention recognizes managed certificates and abandoned temporary files. It can finish interrupted publication, and erasure retains a pending entry when an unsafe file still exists. |
| 7 | Low | Text fallback downloads were labelled PNG and missing attachments could be reported as sent. | Return the actual media type with attachment disposition, nosniff and no-store. Fail mail delivery before SMTP if a requested attachment is missing or malformed. |

### Compatibility and verification

- Full backend run using `venv/Scripts/python -m pytest -q -rs -p no:cacheprovider --basetemp=<fresh-writable-directory>` finished with **622 passed, 14 skipped and 120 warnings**. Eleven skips require disposable PostgreSQL fixtures, one requires Redis, one uses filenames unavailable on Windows and one requires Windows symlink privileges. The final session and retention cases added after collection passed in the focused runs below.
- Deploy the browser client and API together. HTTPS users need one fresh sign-in when switching from the legacy cookie. Originless clients sending a refresh cookie must set Content-Type: application/json on refresh and logout. Approved cross-origin browser deployments must remain compatible with SameSite=Strict. The access-token lifetime and password recovery flow retain their existing behavior.
- Certificate download is a complete bounded attachment. The API and SPA have no upload handler. Administrators retain generate, list, download, email and delete permissions. Donors receive certificates by email. The file endpoint does not authorize downloads using a donor login or the refresh cookie. Keep certificate storage private to the application and scheduler, on a filesystem supporting hard links. Check existing volumes for oversized or damaged legacy files before rollout. No migration or credential rotation is required for these changes.
- The Edge HTTPS test used an isolated SQLite database, temporary self-signed certificate, loopback Uvicorn and Windows Nginx 1.30.7 from the official nginx.org download. It exercised the repository's actual Nginx API location on non-default ports. It verified same-site cross-origin logout rejection, login and rotation, host-bound cookies, administrator download, anonymous and donor download denial, and logout. TLS trust for this temporary certificate was explicitly bypassed in the test browser. Production certificates, deployed proxy configuration and live SMTP remain unverified.
- The browser command ran tests/browser_https_session.py, tests/browser_api_security.py, tests/browser_donor_reset.py, tests/browser_enrollment.py, tests/browser_output_safety.py and tests/browser_erasure.py with pytest and the installed Edge executable. All seven workflows passed. The initial HTTPS harness failed to start Nginx because its temporary directory was missing. Creating the test directory fixed it.
- A focused pytest run of session origin, certificates, file hardening, erasure, refresh sessions, deployment and security regressions passed 103 tests with two Windows-specific skips. A subsequent origin and file hardening run passed 25 with the same two skips, including interrupted publication cleanup. Counts overlap. An earlier email regression used text as a synthetic PNG. Its fixture now creates a real PNG and retains its HTML escaping assertions.
- In frontend, npm.cmd test passed all 34 tests. npm.cmd run lint and npm.cmd run build passed with the existing Vite bundle-size warning. The fatal Ruff gate and git diff --check passed. No additional runtime dependency was introduced.


## Task 8. HTTP headers, logging and public errors

| Severity | Finding | Implementation and evidence |
| --- | --- | --- |
| Medium | HTTP access logs and some diagnostic paths could record query values, provider details or account identifiers. | Nginx records method, status, bytes and duration. Container Uvicorn access logging is disabled. Application logs retain event and exception class. Third-party request logs are restricted. Log regressions exercise sensitive inputs and the browser proxy check inspects the access log. |
| Medium | Public errors could reflect internal exception text. | Domain and unexpected errors return controlled messages. Unexpected failures include a correlation ID. Tests exercise diagnostics and verify private markers stay out of public responses and logs. |
| Low | Header coverage differed between normal API responses, preflights and proxy errors. | The outer application middleware and Nginx set restrictive policies on error paths. The API denies content by default and explicitly enabled documentation uses a separate policy. HTTPS responses include HSTS. The SPA retains its own resource policy. The obsolete browser XSS filter header was removed. |

## Task 9. Secrets, configuration and dependencies

| Severity | Finding | Implementation and evidence |
| --- | --- | --- |
| Medium | Permissive staging defaults and unbounded session lifetimes could weaken production-like deployments. | Startup normalizes the environment, restricts signing to HS256, bounds access and refresh lifetimes, and requires appropriate Redis, SMTP TLS and reCAPTCHA configuration for staging and production. Configuration tests cover acceptance and rejection. See `docs/setup.md` for operator settings. |
| High upstream, conditional applicability | The development pin for Black 26.5.1 carried an advisory affecting its GitHub Action. This repository did not invoke the affected action. | Updated the development pin to 26.10.1 and included development and Redis requirements in CI auditing. [Maintainer advisory](https://github.com/psf/black/security/advisories/GHSA-cg8m-r9f2-5wm2) |
| High, historical release blocker | Phase 1 records a database dump containing personal data and password hashes in repository history. | An owner must scope exposure, reset affected passwords, revoke affected sessions, rotate confirmed exposed credentials and coordinate history cleanup under `docs/HISTORY_SCRUB.md`. A clean secret-pattern scan cannot close this incident. |

## Task 10. Final verification and production readiness

| Command or check | Observed result |
| --- | --- |
| `python -m pytest -q -ra -p no:cacheprovider --basetemp=<fresh-directory>` | 648 passed, 2 Windows filesystem skips, 120 warnings. The run used isolated SQLite fixtures and disposable PostgreSQL 18 and Redis 7.4.11 for tests requiring those services. |
| Alpine Linux 6.18.60, Python 3.11.18: `python -m pytest -q -rs -p no:cacheprovider --noconftest tests/test_certificate_hardening.py` | All 20 passed with one Pydantic deprecation warning. This included both Windows skips on a native Linux filesystem in an isolated software-emulated guest. |
| `python -m pytest -q tests/browser_*.py` (six browser modules supplied explicitly) | Seven Edge journeys passed with built frontend assets and isolated test data, including donor enrollment/recovery, administrator and blood-request workflows, output safety, HTTPS sessions and certificate access. The HTTPS case used Nginx and a local test certificate. |
| Frontend `npm.cmd test`, `npm.cmd run lint`, `npm.cmd run build` | 34 tests passed. ESLint and the Vite production build succeeded. Vite emitted a bundle-size warning. |
| `python -m ruff check --select E9,F63,F7,F82 app migrations tests` and `git diff --check` | Passed. |
| `python -m mypy app` using the repository configuration | Failed with 203 diagnostics in 36 files. The development baseline had 207 in 37 files using the same checker. Comparison by file, enclosing definition and message found no additional diagnostic. Existing type debt remains open. |
| `python -m pip wheel --no-deps --wheel-dir <temporary-directory> .` and `python -m pip check` | Backend wheel built using isolated build dependencies. Installed package consistency passed. |
| `python -m pip_audit -r requirements.txt -r requirements-redis.txt`, repeated with `-r requirements-dev.txt`; frontend `npm.cmd audit --audit-level=low` | Python audits reported no known advisories after the Black update. npm reported zero advisories for its audited dependency tree. |
| `python -m pip_audit --no-deps --disable-pip -r <exact-version-list>` | Checked registry versions from uv.lock and the optional Redis dependency. The two platform alternatives for deprecated required separate lists. Both audits reported no known advisories. |
| Gitleaks 8.30.1, redacted scans of the project source and all locally available Git refs | No matching secret patterns reported. Stored credentials and past personal-data exposure require separate owner review. |

New or extended regression suites cover runtime policy, safe diagnostics, log hygiene, browser session rotation, registration, API authorization, validation, throttling, certificate handling and legitimate workflows. The per-task sections above document the exercised controls. Counts from focused and full runs overlap.

**Release decision.** Hold production approval. Docker image builds and scans, deployed TLS and proxy settings, production Redis access controls, real mail delivery, reCAPTCHA and Maps are unverified here. Before rollout, verify these in staging, deploy the matching frontend and API, configure a trusted origin and signing secret, and close the Phase 1 history incident and privacy/retention approvals. The local verification used isolated databases and synthetic identities. No credentials or live infrastructure were changed.

## Exact files changed across Tasks 1 through 10

- `.env.example`
- `.github/workflows/ci.yml`
- `Dockerfile`
- `PHASE_2_COMPLETION_REPORT.md`
- `app/api/auth/AUTH_README.md`
- `app/api/auth/deps.py`
- `app/api/auth/router.py`
- `app/api/v1/admins.py`
- `app/api/v1/blood_requests.py`
- `app/api/v1/certificates.py`
- `app/api/v1/donors.py`
- `app/api/v1/health.py`
- `app/api/v1/hospitals.py`
- `app/api/v1/privacy.py`
- `app/api/v1/queries.py`
- `app/api/v1/router.py`
- `app/config.py`
- `app/core/api_limits.py`
- `app/core/exceptions.py`
- `app/core/logging.py`
- `app/core/middleware.py`
- `app/core/rate_limiter.py`
- `app/core/recaptcha.py`
- `app/main.py`
- `app/repositories/admin.py`
- `app/repositories/donor.py`
- `app/repositories/hospital.py`
- `app/schemas/admin.py`
- `app/schemas/blood_request.py`
- `app/schemas/donor.py`
- `app/schemas/query.py`
- `app/schemas/validation.py`
- `app/services/certificate_service.py`
- `app/services/distance_service.py`
- `app/services/email_service.py`
- `app/services/erasure_service.py`
- `app/services/otp_service.py`
- `app/services/refresh_session_service.py`
- `app/tasks/scheduled_jobs.py`
- `docker-compose.yml`
- `docs/SyntheticData.sql`
- `docs/initial_data.sql`
- `docs/setup.md`
- `frontend/Dockerfile`
- `frontend/nginx-production.conf.template`
- `frontend/nginx-site.conf`
- `frontend/nginx-upstream.conf`
- `frontend/nginx.conf`
- `frontend/src/pages/AddNewHospital.jsx`
- `frontend/src/pages/AdminLogin.jsx`
- `frontend/src/pages/AdminSignup.jsx`
- `frontend/src/pages/DonorLogin.jsx`
- `frontend/src/pages/FetchDonors.jsx`
- `frontend/src/pages/GenerateCertificate.jsx`
- `frontend/src/pages/GenerateRequests.jsx`
- `frontend/src/pages/ManageHospitalDetails.jsx`
- `frontend/src/pages/NewRequestsAdmin.jsx`
- `frontend/src/pages/QueryPageAdmin.jsx`
- `frontend/src/pages/QueryPageDonor.jsx`
- `frontend/src/pages/RegisterDonor.jsx`
- `frontend/src/services/api/auth.js`
- `frontend/src/services/http.js`
- `frontend/src/services/http.test.js`
- `frontend/src/services/requests.js`
- `frontend/src/services/requests.test.js`
- `pyproject.toml`
- `requirements-dev.txt`
- `requirements.txt`
- `scripts/load_dev_data.py`
- `tests/browser_api_security.py`
- `tests/browser_donor_reset.py`
- `tests/browser_enrollment.py`
- `tests/browser_https_session.py`
- `tests/browser_output_safety.py`
- `tests/conftest.py`
- `tests/contract/openapi_snapshot.json`
- `tests/helpers.py`
- `tests/test_aadhaar_removal.py`
- `tests/test_account_rate_limits.py`
- `tests/test_admin_password_reset.py`
- `tests/test_admin_roles.py`
- `tests/test_admin_safeguards.py`
- `tests/test_api_limits.py`
- `tests/test_authorization_matrix.py`
- `tests/test_certificate_hardening.py`
- `tests/test_certificates.py`
- `tests/test_config_validation.py`
- `tests/test_deploy_config.py`
- `tests/test_diagnostics.py`
- `tests/test_domain_validation.py`
- `tests/test_donors.py`
- `tests/test_email_normalization.py`
- `tests/test_enrollment.py`
- `tests/test_erasure.py`
- `tests/test_error_responses.py`
- `tests/test_legacy_hash.py`
- `tests/test_load_dev_data.py`
- `tests/test_log_hygiene.py`
- `tests/test_mass_assignment.py`
- `tests/test_password_handling.py`
- `tests/test_phase2_runtime_security.py`
- `tests/test_query_ownership.py`
- `tests/test_refresh_race.py`
- `tests/test_refresh_sessions.py`
- `tests/test_security_regressions.py`
- `tests/test_seed_data.py`
- `tests/test_session_origin.py`
- `tests/test_session_revocation.py`
- `uv.lock`
