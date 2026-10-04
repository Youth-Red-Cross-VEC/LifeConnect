# Project Setup Guide for LifeConnect

This guide will walk you through the setup process for running the LifeConnect project locally.
The project uses **FastAPI** for the backend and **React/Vite** for the frontend.

## Prerequisites

Ensure that the following are installed on your system:

- **Python 3.11+** (the Docker image and `pyproject.toml` both target 3.11)
- **uv**: Fast Python package installer and resolver.
- **Node.js (v18+) and npm**: For running the frontend.
- **PostgreSQL 14+**: required. The quickest way is `docker compose up postgres`. SQLite is not a supported
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

2. Copy `.env.example` to `.env` and fill in the values. The settings are read by `app/config.py`:
   ```plaintext
   APP_ENV=development
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/lifeconnect
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
   Migration `0005` drops the retired `personal_details.aadhar_number` column. It refuses to run while
   any row still holds a value; back up the database and re-run with
   `LIFECONNECT_ALLOW_AADHAAR_DROP=1 alembic upgrade head` to confirm.

4. (Optional) Load synthetic development data from `docs/initial_data.sql`. Every account in it uses the
   dev-only password `DevOnly#2026`. Never load it into a production database.

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
| `APP_ENV` | `development` | `production` (requires `RECAPTCHA_SECRET_KEY` and a 32+ character `SECRET_KEY`) |
| `SCHEDULER_ENABLED` | `false` | `false` on every web worker; `true` on exactly **one** dedicated scheduler process (`docker compose` runs it as the `scheduler` service) |
| `RECAPTCHA_ENFORCED` | `false` | `true`: login requires a valid `recaptcha_token` and fails closed with 400 |
| `RATE_LIMIT_PER_MINUTE` | `60` | Default per-IP limit for routes without their own limit |
| `RATE_LIMIT_STORAGE_URI` | `memory://` | `memory://` counts per process; with more than one worker or replica use a shared store such as `redis://host:6379/0` (needs the `redis` Python package) |
| `DONOR_ELIGIBILITY_DAYS` | `60` | Days a donor stays inactive after donating |

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
