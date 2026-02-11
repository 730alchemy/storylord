"""Storylord Characters REST API."""

import uvicorn

from api.app import create_app
from config import get_settings

__all__ = ["create_app", "main"]


def main() -> None:
    """Entry point for running the API server."""
    app = create_app()
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
