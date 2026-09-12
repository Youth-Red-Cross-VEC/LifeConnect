# Project Setup Guide for LifeConnect

This guide will walk you through the setup process for running the LifeConnect project locally.
The project uses **FastAPI** for the backend and **React/Vite** for the frontend.

## Prerequisites

Ensure that the following are installed on your system:

- **Python 3.10+**
- **uv**: Fast Python package installer and resolver.
- **Node.js (v18+) and npm**: For running the frontend.
- **PostgreSQL**: (Optional) For running the database locally, or use SQLite (default for development).

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
   
   uv pip install -r pyproject.toml
   ```

2. Create a `.env` file in the root directory based on `.env.example` (or use the defaults for local SQLite):
   ```plaintext
   # Example backend .env
   ENVIRONMENT=development
   DATABASE_URL=sqlite+aiosqlite:///./test.db
   SECRET_KEY=your_super_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   
   # Email settings
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

3. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend will be available at `http://localhost:8000`.

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
