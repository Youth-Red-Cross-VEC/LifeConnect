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
   `python scripts/load_dev_data.py --full` (2 admins, 10 donors, hospitals and requests). Every account uses the
   published dev-only password `DevOnly#2026`, so the loader refuses `APP_ENV=production` and refuses any database
   that already holds an admin or a donor. Do not pipe `docs/*.sql` into `psql` by hand: that has no guard.

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
| `DOCS_ENABLED` | unset (docs on) | unset (docs off); `true` switches them on explicitly |
| `SCHEDULER_ENABLED` | `false` | `false` on every web worker; `true` on exactly **one** dedicated scheduler process (`docker compose` runs it as the `scheduler` service) |
| `RECAPTCHA_ENFORCED` | `false` | `true`: login **and the public blood-request form** require a valid `recaptcha_token` and fail closed with 400 |
| `RATE_LIMIT_PER_MINUTE` | `60` | Default per-IP limit for routes without their own limit |
| `BLOOD_REQUEST_RATE_LIMIT` | `5/minute;30/hour` | Dedicated per-IP limit on the public blood-request form (it emails the admins) |
| `ADMIN_NOTIFY_MAX_RECIPIENTS` | `20` | A new request sends ONE email, BCC'd to at most this many active admins |
| `OTP_TTL_SECONDS` / `OTP_MAX_ATTEMPTS` | `600` / `5` | The attempt budget belongs to the window: requesting a new code does not reset it, so after the allowed wrong guesses a user waits for the window to end |
| `RATE_LIMIT_STORAGE_URI` | `memory://` | `memory://` counts per process; with more than one worker or replica use a shared store such as `redis://host:6379/0` (install `pip install -r requirements-redis.txt` first; startup refuses to run without it; in Docker add it to the Dockerfile's install list) |
| `DONOR_ELIGIBILITY_DAYS` | `60` | Days a donor stays inactive after donating |

### Docker deployment

`docker-compose.yml` publishes **only the frontend (nginx, port 80)**. PostgreSQL and the API are reachable on the
compose network only. Before the first `docker compose up`:

- Put `POSTGRES_PASSWORD` in `.env` (long and random). It has no default; compose refuses to start without it.
- Put a real `SECRET_KEY` in `.env` (see step 2). `APP_ENV=production` also needs `RECAPTCHA_SECRET_KEY` and
  `RECAPTCHA_ENFORCED=true`.
- For debugging from your machine, add the loopback-only override. It publishes PostgreSQL and the API on
  `127.0.0.1` and nothing else: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`. Never use it
  on a server.

**Client IP behind nginx.** The API sits behind the nginx container, so rate limits only work per client if uvicorn
reads the real address from `X-Forwarded-For`, and only from nginx. Uvicorn runs with `--proxy-headers`, and
`FORWARDED_ALLOW_IPS` is the single trusted address: the frontend container, pinned to `172.28.0.10` in
`docker-compose.yml`. Any other peer's `X-Forwarded-For` is ignored. Never set it to `*`. If your host already uses
`172.28.0.0/24`, change the subnet and the frontend address together and set `FORWARDED_ALLOW_IPS` to match. A
different reverse proxy or a load balancer in front of nginx changes this: trust exactly the address that connects
to the API.

**SPA security headers.** `frontend/security-headers.conf` adds a Content-Security-Policy, `X-Frame-Options`,
`X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` and HSTS to every SPA response. HSTS is only
honoured over HTTPS, so it does nothing until TLS is terminated in front of (or in) nginx. The CSP allows exactly
the origins the frontend uses (reCAPTCHA, Google Fonts, Font Awesome from cdnjs). If you add a third-party script,
font or API origin, extend it, and check the browser console for CSP violations on the login, landing and signup
pages.

**Dependencies in the image.** The API image installs `requirements-runtime.lock` (hash-pinned) with a
version-and-digest-pinned `uv`; see `docs/supply-chain.md` for how to update it and which images and GitHub Actions
still need their digests/SHAs pinned.

### Sessions, passwords and accounts

- **Logout and access tokens.** Logging out revokes the refresh token on the server (`POST /auth/logout` works
  without a valid access token). An access token that was already issued stays valid until it expires
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, 30 by default), so log out on shared computers and keep that value short. The
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
