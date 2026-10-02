# syntax=docker/dockerfile:1
#
# Multi-stage build. The builder compiles wheels; the final stage ships
# only the runtime. Result: a much smaller image with no build tooling
# and no dev dependencies in production.

# -----------------------------------------------------------------------------
# STAGE 1 — builder: compile wheels
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS builder

WORKDIR /build

# Compiling psycopg2 requires build tools, which we deliberately do NOT
# carry into the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the dependency manifest first. Docker caches this layer, so
# editing application code does NOT re-run pip install.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.txt

# -----------------------------------------------------------------------------
# STAGE 2 — final: runtime only
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS final

LABEL org.opencontainers.image.title="PortfolioX" \
      org.opencontainers.image.description="Layered portfolio-trading backend" \
      org.opencontainers.image.source="https://github.com/atharva486/PortfolioX"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Runtime shared libraries only — no compiler toolchain.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Install from the pre-built wheels, then remove the wheelhouse.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application code only.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Drop root. Never run a web server as root.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# /health should answer "is this process alive?", not "is the DB reachable?"
# Liveness must not depend on a downstream service.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]