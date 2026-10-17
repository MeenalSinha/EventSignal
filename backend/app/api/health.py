"""Health endpoint: reports the real state of the API and its database."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.database import check_connection, missing_tables
from app.schemas.health import ComponentHealth, HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


def _check_database(engine: Engine) -> ComponentHealth:
    try:
        check_connection(engine)
    except (SQLAlchemyError, OSError):
        # Details are logged server-side; the response stays free of paths and credentials.
        logger.exception("Database connectivity check failed")
        return ComponentHealth(status="unavailable", message="Database connection failed.")

    try:
        absent = missing_tables(engine)
    except (SQLAlchemyError, OSError):
        logger.exception("Database schema check failed")
        return ComponentHealth(status="unavailable", message="Database schema check failed.")

    if absent:
        return ComponentHealth(
            status="degraded",
            message=f"Database reachable but {len(absent)} expected table(s) are missing.",
        )
    return ComponentHealth(status="ok", message="Database reachable and schema present.")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health",
    description=(
        "Returns 200 only when every required check passes. Returns 503 with the same "
        "body shape when the database is unreachable or its schema is incomplete."
    ),
    responses={503: {"model": HealthResponse, "description": "Service not healthy."}},
)
def get_health(request: Request, response: Response) -> HealthResponse:
    settings: Settings = request.app.state.settings
    database = _check_database(request.app.state.engine)

    if database.status == "ok":
        overall, message = "healthy", "All checks passed."
    elif database.status == "degraded":
        overall, message = "degraded", "Service is running with an incomplete database schema."
    else:
        overall, message = "unhealthy", "A required dependency is unavailable."

    if overall != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall,  # type: ignore[arg-type]
        message=message,
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        checked_at=datetime.now(UTC),
        components={
            "api": ComponentHealth(status="ok", message="API responding."),
            "database": database,
        },
    )
