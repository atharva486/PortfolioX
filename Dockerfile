# syntax=docker/dockerfile:1
#
# Multi-stage build: the builder prepares wheels, the final stage ships
# only the runtime. The production image contains no compiler and no dev
# tooling (ruff, mypy, pytest are all excluded via requirements-prod.txt).
#
# Result: a small, hardened image that cannot accidentally run tests.

# -----------------------------------------------------------------------------
# STAGE 1 — builder: resolve dependencies into wheels
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS builder

WORKDIR /build

# psycopg2-binary ships manylinux wheels, so no compiler is needed here
# either. Copying the manifest first means editing app code does NOT
# invalidate this layer.
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements-prod.txt

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

# libpq5 at runtime for psycopg2; curl for the healthcheck below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Install from prebuilt wheels only (--no-index guarantees no network
# resolution happens here), then delete the wheelhouse.
COPY --from=builder /wheels /wheels
COPY requirements-prod.txt .
RUN pip install --no-index --find-links=/wheels -r requirements-prod.txt \
    && rm -rf /wheels

# Application code only. Tests, scripts, and docs are excluded by
# .dockerignore so they never enter the build context.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Run as a non-root user. A compromised process should not own the app.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness only: /health does NOT touch the database. A liveness probe
# that depends on Postgres would restart the app during a DB blip,
# turning a partial outage into a full one.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# --host 0.0.0.0 is required in a container. Binding to localhost would
# make the service unreachable from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]