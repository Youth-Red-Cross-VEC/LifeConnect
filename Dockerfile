# LifeConnect API - Ultra-optimized Multi-stage Dockerfile
# Target: Minimal production image size

# Stage 1: Build dependencies with full toolchain
FROM python:3.11-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /build

# Install build dependencies (will not be in final image)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    curl \
    # Pillow dependencies
    jpeg-dev \
    zlib-dev \
    libjpeg

# Install uv for fast package installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install Python dependencies to isolated directory
RUN uv pip install --target=/deps \
    fastapi uvicorn[standard] \
    pydantic pydantic-settings email-validator \
    sqlalchemy[asyncio] asyncpg alembic \
    python-jose[cryptography] passlib[bcrypt] python-multipart \
    apscheduler httpx aiosmtplib \
    structlog slowapi python-dotenv pillow

# Remove unnecessary files from deps to reduce size
RUN find /deps -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /deps -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /deps -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /deps -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /deps -type f -name "*.pyo" -delete 2>/dev/null || true && \
    find /deps -type f -name "*.so" -exec strip {} \; 2>/dev/null || true

# Stage 2: Minimal production image
FROM python:3.11-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/deps

WORKDIR /code

# Install ONLY runtime dependencies (minimal)
RUN apk add --no-cache \
    libpq \
    libjpeg \
    zlib \
    && adduser -D -u 1000 appuser

# Copy dependencies from builder
COPY --from=builder /deps /deps

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
