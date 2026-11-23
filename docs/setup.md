# Project Setup Guide for LifeConnect

This guide will walk you through the setup process for running the LifeConnect project locally.
The project uses **FastAPI** for the backend and **React/Vite** for the frontend.

## Prerequisites

Ensure that the following are installed on your system:

- **Python 3.11+** (the Docker image and `pyproject.toml` both target 3.11)
- **uv**: Fast Python package installer and resolver.
- **Node.js (v18+) and npm**: For running the frontend.
- **PostgreSQL 14+**: required. The quickest way is the loopback-only dev override (set `POSTGRES_PASSWORD`
  in `.env` first; see "Docker deployment" below):
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres`. SQLite is not a supported
  database for the app (it is only used by the automated tests).

## Setup Steps

### 1. Clone the Repository

Start by cloning the project repository:

```bash
git clone https://github.com/your-repo-url/lifeconnect.git
cd lifeconnect
```

### 2. Backend Setup

The backend uses `uv` for dependency management.

1. Create a virtual environment and install dependencies:
   ```bash
   uv venv
   # Activate the virtual environment (Windows)
   .venv\Scripts\activate
   # Activate the virtual environment (Mac/Linux)
   source .venv/bin/activate

   uv pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in the values. The settings are read by `app/config.py`.
   **The app will not start until `SECRET_KEY` is a real secret**: it must be at least 32 characters and must
   not be a placeholder (`CHANGE_ME`, `your-secret-key-here`, ...), in every environment. Generate one with
   `python -c "import secrets; print(secrets.token_hex(32))"`. The test suite pins its own key and never reads
   your `.env`, so the steps in this guide work on a fresh clone.
   ```plaintext
   APP_ENV=development
   DATABASE_URL=postgresql+asyncpg://lifeconnect:<your POSTGRES_PASSWORD>@localhost:5432/lifeconnect
   SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=30

   # Email settings (note the MAIL_ prefix)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   MAIL_FROM=your_email@gmail.com
   MAIL_USE_TLS=True

   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   ```

3. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```
   `alembic upgrade head` never destroys data and is safe to run on every start. The retired
   `personal_details.aadhar_number` column is left in place (nullable) so old values are not lost
   by accident. To remove it permanently, take a backup and then run, deliberately:
   `LIFECONNECT_ALLOW_AADHAAR_DROP=1 python scripts/drop_aadhaar_column.py --i-have-a-backup`
   (it prints how many rows hold a value and refuses without both the env flag and the backup flag).

4. (Optional) Load synthetic development data with `python scripts/load_dev_data.py` (bootstrap admin only) or
   `python scripts/load_dev_data.py --full` (2 admins, 10 donors, hospitals and requests). Password login is disabled for these accounts by default.
   Set a private `DEV_SEED_PASSWORD` in the loader process environment if local login is needed.
   The loader refuses production and any database that already holds an admin or donor.

5. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend will be available at `http://localhost:8000`.

6. (Optional) Run the background jobs (request expiry, donor reactivation, age increments) in a separate
   process: set `SCHEDULER_ENABLED=true` and run `python -m app.scheduler_worker`.

### Deployment settings

| Setting | Dev / test | Production |
| ------- | ---------- | ---------- |
| `SECRET_KEY` | A generated key, 32+ characters | Same, in **every** environment. Placeholders and short keys are rejected at startup. |
| `APP_ENV` | `development` | `production`: requires `RECAPTCHA_SECRET_KEY` **and** `RECAPTCHA_ENFORCED=true`, and turns `/docs`, `/redoc` and `/openapi.json` off |
| `ENABLE_DOCS` | unset (docs on) | unset (docs off); `true` switches them on explicitly |
| `SCHEDULER_ENABLED` | `false` | `false` on every web worker; `true` on exactly **one** dedicated scheduler process (`docker compose` runs it as the `scheduler` service) |
| `RECAPTCHA_ENFORCED` | `false` | `true`: login **and the public blood-request form** require a valid `recaptcha_token` and fail closed with 400 |
| `RATE_LIMIT_PER_MINUTE` | `60` | Default per-IP limit for routes without their own limit |
| `AUTH_RATE_LIMIT` | `5/minute` | Per IP and operation for login, registration and reset confirmation |
| `PASSWORD_RESET_RATE_LIMIT` | `3/minute` | Per IP and operation for reset, enrollment and invitation code delivery |
| `ACCOUNT_AUTH_RATE_LIMIT` | `10/10 minutes` | Across IPs for the same canonical email and login, registration or reset-confirmation operation |
| `ACCOUNT_CODE_SEND_RATE_LIMIT` | `3/10 minutes` | Across IPs for a recipient and code-delivery operation |
| `SUPPORT_QUERY_RATE_LIMIT` | `5/minute;30/hour` | Per IP for support query submission |
| `BLOOD_REQUEST_RATE_LIMIT` | `5/minute;30/hour` | Dedicated per-IP limit on the public blood-request form (it emails the admins) |
| `ADMIN_NOTIFY_MAX_RECIPIENTS` | `20` | A new request sends ONE email, BCC'd to at most this many active admins |
| `OTP_TTL_SECONDS` / `OTP_MAX_ATTEMPTS` | `600` / `5` | The attempt budget belongs to the window: requesting a new code does not reset it, so after the allowed wrong guesses a user waits for the window to end |
| `RATE_LIMIT_STORAGE_URI` | `memory://` | `memory://` counts per process. The production overlay uses private Redis. For a host install with Redis, install `pip install -r requirements-redis.txt` first. **`APP_ENV=production` refuses to start with `memory://`.** |
| `DONOR_ELIGIBILITY_DAYS` | `60` | Days a donor stays inactive after donating |

Each operation has its own budget. Account counters use a keyed digest of the normalized address. IP counters use the ASGI peer after Uvicorn applies its trusted-proxy rules. IPv4-mapped addresses share their IPv4 bucket, and IPv6 clients share a bucket within a /64. Keep Nginx as the only trusted forwarding peer. A quota rejection from the IP or account limiter includes a Retry-After duration in seconds. Keep the same signing secret and Redis configuration across replicas. Each worker uses the same Redis database in the production Compose overlay.

### Docker deployment

For local Docker use, set the generated `SECRET_KEY` and `POSTGRES_PASSWORD` in `.env`, then run
`docker compose up --build`. The base file serves the frontend at `http://127.0.0.1` and requires no TLS files.
Leave the frontend site key empty if local reCAPTCHA enforcement is off. Add `docker-compose.dev.yml`
only for local debugging when you need the API or PostgreSQL published on loopback.

On the production host, use Docker Compose 2.24.4 or later and combine the base and production files.
Allow public access to TCP 80 and 443 and point the approved DNS name at the host. The production overlay
enforces production mode, reCAPTCHA, private Redis rate limiting and disabled debug mode and API docs.
The frontend and API share an origin. If a separate HTTPS client requires CORS, set
`PRODUCTION_ALLOWED_ORIGINS` to a JSON array of exact HTTPS origins. Its default is `[]`.

Set these in the host's protected `.env` file, using values issued for this deployment:

| Setting | Value |
| --- | --- |
| `LIFECONNECT_DOMAIN` | Lowercase public DNS hostname, without a scheme, path or port |
| `LIFECONNECT_TLS_DIR` | Absolute path to the dedicated host certificate directory |
| `VITE_RECAPTCHA_SITE_KEY` | Public reCAPTCHA v3 site key registered for the production hostname |
| `RECAPTCHA_SECRET_KEY` | Matching server key, supplied as a secret at runtime |
| `SECRET_KEY`, `POSTGRES_PASSWORD` | Independently generated secrets. Use URL-safe characters in the database password because Compose builds a database URL. |

Provision the existing mail and Maps configuration as well. Rebuild the frontend when the public site
key changes. Only variables named in the frontend build arguments are needed for the browser bundle.

**Certificate installation and renewal.** Obtain a CA-issued certificate for the configured hostname.
Use DNS validation for initial issuance so certificate setup does not depend on an already running HTTPS
server. For unattended renewal, configure an ACME client with the supported plugin for your DNS provider
and a restricted DNS credential. Copy the certificate chain and matching key into the dedicated directory
as `fullchain.pem` and `privkey.pem`. On a Linux host, restrict the directory and private key to the
deployment administrator and Nginx master. Compose mounts this directory read-only in the frontend.

```sh
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T frontend nginx -t
```

For Certbot, configure a deploy hook to run after successful renewal of this certificate. Copy the new
pair from `$RENEWED_LINEAGE` into temporary files in the mounted host directory, set restrictive
permissions, then rename them to the installed filenames. Keep a protected copy of the previous
matching pair until the reload succeeds. From the deployment directory, run:

```sh
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T frontend nginx -t &&
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T frontend nginx -s reload
```

Test renewal with `certbot renew --dry-run` and exercise the deployment hook in staging. Monitor
certificate expiry and renewal and reload failures. If validation fails, restore the previous pair before
retrying. Verify the public hostname presents a valid chain, HTTP redirects to HTTPS, TLS 1.2 and 1.3
work, HTTPS sends HSTS, and the login and blood request forms complete reCAPTCHA. For a code rollback,
redeploy the previous verified HTTPS images and configuration. Keep the PostgreSQL and Redis volumes.
See the [Certbot renewal and hooks guide](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates).

**Proxy boundary.** Nginx replaces the incoming forwarding headers with its own connection values.
Uvicorn trusts only the pinned Nginx address, `172.28.0.10`. PostgreSQL and Redis join an isolated
data network, and the API has no published ports in production. If you put a load balancer or CDN in
front of Nginx, restrict direct ingress and configure Nginx to trust only that provider's verified addresses
before using its client IP metadata. Keep Uvicorn's trust limited to Nginx.

The CSP allows the required reCAPTCHA, font and icon hosts. Google documents the required paths in its
[reCAPTCHA CSP guidance](https://developers.google.com/recaptcha/docs/faq#im_using_content-security-policy_csp_on_my_website._how_can_i_configure_it_to_work_with_recaptcha).
HSTS is sent on HTTPS responses, including
API and static asset responses. Production refresh cookies are Secure, HttpOnly and SameSite=Strict.
The API image installs the pinned runtime sets in `requirements.txt` and `requirements-redis.txt`.

Staging and production require SMTP TLS, a configured mail credential, enforced reCAPTCHA and Redis rate-limit storage. Configure the signing key using a secret manager. The supported signing algorithm is HS256. Access-token lifetimes are bounded to 1?1,440 minutes and refresh-token lifetimes to 1?30 days. Unrecognized environment names fail startup.

The Nginx access log records method, status, response bytes and elapsed time. The API container disables the duplicate Uvicorn access log. Use the error ID returned on an application failure to correlate it with the server event.

### Sessions, passwords and accounts

- **Logout and access tokens.** Logging out revokes the refresh token on the server (`POST /auth/logout` works
  without a valid access token). HTTPS deployments use the host-only `__Host-lc_refresh_token` cookie
  with Path=/, Secure, HttpOnly and SameSite=Strict. Development uses the auth-path cookie. On rollout,
  HTTPS users must sign in once to obtain the new cookie. Non-browser clients without an Origin must send
  `Content-Type: application/json` on cookie-bearing refresh and logout. Access tokens are held in browser memory. An access token stays valid until it expires
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, 15 by default), so log out on shared computers. The
  donor dashboard has a **Log out** button.
- **Revocation.** A successful password reset, and deactivating an admin or donor, revoke **all** of that account's
  refresh sessions. A refresh token can be spent only once even if two requests race (the second one revokes the
  chain, as for any reuse).
- **Passwords** are limited to 72 **bytes** (UTF-8), the most bcrypt can hash faithfully, so a password of 25
  emoji is too long. Choosing a password (registration and reset) also needs 8+ characters, an uppercase letter and
  a digit.
- **Email addresses** are compared case-insensitively and stored in lowercase. A unique index on `lower(email)`
  (migration `0008`) enforces it. If an existing database already has two donor accounts whose emails differ only by
  case, `alembic upgrade head` stops with an error that lists them and changes nothing; merge or rename the extra
  accounts, then run it again. To list them yourself:
  `SELECT id, email FROM donor_details WHERE lower(email) IN (SELECT lower(email) FROM donor_details GROUP BY lower(email) HAVING count(*) > 1);`
  A donor cannot register with an address an admin uses.
- **Support queries** belong to the signed-in donor who filed them (`query_table.donor_id`, migration `0007`).
  Queries filed anonymously, and every query that existed before that migration, have no owner: admins see them,
  `GET /queries/my-queries` does not.

### Background jobs

- Donor ages are recomputed from the date of birth every night, so the job is safe to run twice or late. Someone
  born on 29 February turns a year older on **1 March** in non-leap years.
- Jobs may start up to 6 hours late (container restart, deploy) and missed runs are coalesced into one.

### Running the tests

`python -m pytest -q` needs nothing but `pip install -r requirements.txt`. Two groups of tests only run against a
real PostgreSQL, because they exercise Postgres-specific behaviour (advisory locks, migrations). Point
`MIGRATION_TEST_DATABASE_URL` at an **empty throwaway** database, for example:

```bash
docker run -d --name lc-test-pg -e POSTGRES_PASSWORD=throwaway -e POSTGRES_DB=lc_test -p 127.0.0.1:55432:5432 postgres:16-alpine
MIGRATION_TEST_DATABASE_URL=postgresql+asyncpg://postgres:throwaway@127.0.0.1:55432/lc_test python -m pytest -q
```

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the `frontend/` directory:
   ```plaintext
   VITE_API_URL=http://localhost:8000
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

## Working with Git

To keep your contributions organized, follow these steps:

1. **Create a branch**:
   ```bash
   git checkout -b feature/branch-name
   ```

2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add your commit message here"
   ```

3. **Push the branch**:
   ```bash
   git push origin feature/branch-name
   ```

4. **Create a Pull Request** on GitHub.
