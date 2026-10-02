"""Operational endpoints: health and readiness.

These are what a container orchestrator, load balancer, or uptime monitor
calls. They are NOT part of the business API.
"""

import logging
import os

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ops"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: is this process running and able to serve requests?

    Deliberately does NOT touch the database. A liveness probe that
    depends on a downstream service will restart your app during a
    database blip — turning a partial outage into a full outage.
    """
    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response) -> dict[str, str]:
    """Readiness: should this instance receive traffic right now?

    Unlike /health, this DOES check the database, because an instance
    that cannot reach Postgres cannot serve orders.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        logger.error("Readiness check failed: %s", e)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unreachable"}

    return {"status": "ready", "database": "ok"}


@router.get("/health/db")
def health_db() -> dict[str, str]:
    """Detailed database diagnostics, for manual debugging only.

    Never returns credentials or connection strings.
    """
    dialect = engine.dialect.name
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar() or "unknown"
        return {"database": "ok", "dialect": dialect, "version": version[:60]}
    except SQLAlchemyError as e:
        logger.error("Database health check failed: %s", e)
        return {"database": "unreachable", "dialect": dialect, "error": str(e)[:120]}


@router.get("/version")
def version() -> dict[str, str]:
    """Deployment identity: which commit is actually running?"""
    commit = os.environ.get("GIT_COMMIT_SHA", "unknown")
    return {"service": "portfoliox", "commit": commit}
