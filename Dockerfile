# LifeConnect API - Multi-stage Dockerfile for minimal image size

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /build

# Install build dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml .

# Install dependencies (not editable, just deps)
RUN uv pip install --target=/deps \
    fastapi uvicorn[standard] gunicorn \
    pydantic pydantic-settings email-validator \
    sqlalchemy[asyncio] asyncpg alembic \
    python-jose[cryptography] passlib[bcrypt] python-multipart \
    apscheduler httpx aiosmtplib \
    structlog slowapi python-dotenv pillow

# Stage 2: Production image
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/deps

WORKDIR /code

# Install runtime dependencies only (no gcc, no dev packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Copy installed dependencies from builder
COPY --from=builder /deps /deps

# Copy application code
COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Set ownership
RUN chown -R appuser:appuser /code

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
