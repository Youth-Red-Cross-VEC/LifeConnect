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
    # Pillow dependencies
    jpeg-dev \
    zlib-dev \
    libjpeg

# uv for fast package installation, taken from the official image pinned to an exact release and digest
# instead of piping a downloaded script into a shell. To bump it: change the tag, look up the new digest with
#   docker buildx imagetools inspect ghcr.io/astral-sh/uv:<tag>
# and regenerate requirements-runtime.lock (the command is in requirements-runtime.in).
COPY --from=ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 /uv /bin/uv
RUN uv --version | grep -q '^uv 0.12.23 '

# Install exactly the audited, hash-pinned dependency set: no version is resolved at build time, a package whose
# hash is not in the lock is refused, and --no-deps means nothing outside the lock can sneak in.
COPY requirements-runtime.lock ./
RUN uv pip install --require-hashes --no-deps --target=/deps -r requirements-runtime.lock

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

# Certificates are written at runtime. Create the directory (and own it) here: a volume mounted
# later inherits this ownership, and without it certificate generation failed with a bare
# PermissionError as appuser.
RUN mkdir -p /code/app/static/images/certificates && \
    chown -R appuser:appuser /code/app/static

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# --proxy-headers: honour X-Forwarded-For/-Proto, but only from FORWARDED_ALLOW_IPS (uvicorn's default is
# 127.0.0.1; docker-compose.yml sets it to the nginx container). Never set it to "*".
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
