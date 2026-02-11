"""Application bootstrap helpers."""

from __future__ import annotations

from config import bootstrap_environment, configure_logging, get_settings


def bootstrap():
    """Initialize settings, logging, and environment variables."""
    settings = get_settings()
    bootstrap_environment(settings)
    configure_logging(settings.log_format)
    return settings
