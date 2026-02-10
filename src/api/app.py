"""FastAPI application setup and configuration."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from api.routers import characters

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    log.info("api_server_starting")
    yield
    log.info("api_server_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Storylord Characters API",
        description="REST API for managing character profiles",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(characters.router, prefix="/api/v1")

    return app


# Application instance
app = create_app()
