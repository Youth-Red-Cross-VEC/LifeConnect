# LifeConnect API - Ultra-optimized Multi-stage Dockerfile
# Target: Minimal production image size

# Stage 1: Build dependencies with full toolchain
FROM python:3.11-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies (will not be in final image)
RUN apk upgrade --no-cache && apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    # Pillow dependencies
    jpeg-dev \
    zlib-dev \
    libjpeg

# Install the exact runtime versions pinned in requirements.txt. Development and test tools are
# isolated in requirements-dev.txt and are not copied into the image.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY requirements-redis.txt ./
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements-redis.txt

# Remove unnecessary files from deps to reduce size
RUN find /install -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /install -type f -name "*.pyo" -delete 2>/dev/null || true && \
    find /install -type f -name "*.so" -exec strip {} \; 2>/dev/null || true

# Stage 2: Minimal production image
FROM python:3.11-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/install/lib/python3.11/site-packages

WORKDIR /code

# Install ONLY runtime dependencies (minimal)
RUN apk upgrade --no-cache && apk add --no-cache \
    libpq \
    libjpeg \
    zlib \
    && adduser -D -u 1000 appuser \
    && python -m pip uninstall -y setuptools wheel pip

# Copy dependencies from builder
COPY --from=builder /install /install

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
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-access-log"]
