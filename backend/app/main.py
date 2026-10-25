"""FastAPI application factory and lifecycle."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api import (
    assessment,
    auth,
    health,
    help_offers,
    institutions,
    media,
    opportunities,
    phase7,
    phase8,
    profiles,
)
from app.core.config import PROJECT_ROOT, Settings, get_settings
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

            if settings.demo_mode_enabled:
                from app.services.demo_service import DemoService
                with app.state.session_factory() as db:
                    DemoService.seed_demo_environment(db, settings)
                logger.info("Demo environment prepared and verified")

            if settings.cloudinary_enabled:
                from app.services.media_service import configure_cloudinary
                configure_cloudinary(settings)
                logger.info("Cloudinary media integration initialized (%s)", settings.cloudinary_cloud_name)
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
    app.dependency_overrides[get_settings] = lambda: settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    v1 = APIRouter(prefix=API_V1_PREFIX)
    v1.include_router(health.router)
    v1.include_router(opportunities.router)
    v1.include_router(assessment.router)
    v1.include_router(auth.router)
    v1.include_router(institutions.router)
    v1.include_router(profiles.router)
    v1.include_router(profiles.compat_router)
    v1.include_router(help_offers.router)
    v1.include_router(help_offers.compat_router)
    v1.include_router(phase7.router)
    v1.include_router(phase8.router)
    v1.include_router(media.router)
    v1.include_router(media.inst_router)
    app.include_router(v1)

    # Mount frontend static distribution for unified container deployments
    if settings.app_env != "test":
        dist_dir = PROJECT_ROOT / "frontend" / "dist"
        if not dist_dir.is_dir():
            dist_dir = Path("/app/frontend/dist")
        if dist_dir.is_dir() and (dist_dir / "index.html").is_file():
            assets_dir = dist_dir / "assets"
            if assets_dir.is_dir():
                app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

            @app.get("/{full_path:path}", include_in_schema=False)
            async def serve_frontend_spa(full_path: str) -> FileResponse:
                if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json"}:
                    raise HTTPException(status_code=404, detail="Not Found")
                file_candidate = dist_dir / full_path
                if full_path and file_candidate.is_file():
                    return FileResponse(file_candidate)
                return FileResponse(dist_dir / "index.html")

    return app
