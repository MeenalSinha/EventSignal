"""FastAPI application factory and lifecycle."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api import (
    assessment,
    auth,
    health,
    help_offers,
    institutions,
    opportunities,
    profiles,
)
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.database import (
    create_db_engine,
    create_session_factory,
    ensure_sqlite_directory,
    init_db,
)

logger = logging.getLogger(__name__)

API_V1_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application instance.

    Accepting settings explicitly keeps tests isolated from the developer's
    environment and real database. Run with: ``uvicorn app.main:create_app --factory``.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.resolved_database_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        try:
            ensure_sqlite_directory(settings)
            init_db(engine)
            logger.info("Database initialised (%s)", engine.dialect.name)
        except (SQLAlchemyError, OSError):
            # Keep serving so /health can report the failure honestly.
            logger.exception("Database initialisation failed; health will report it")
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description="AI extracts. Rules evaluate. Evidence explains. Students decide.",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    register_error_handlers(app)

    v1 = APIRouter(prefix=API_V1_PREFIX)
    v1.include_router(health.router)
    v1.include_router(opportunities.router)
    v1.include_router(assessment.router)
    v1.include_router(auth.router)
    v1.include_router(institutions.router)
    v1.include_router(profiles.router)
    v1.include_router(help_offers.router)
    app.include_router(v1)
    return app
