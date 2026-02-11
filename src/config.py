import logging.config
import os
from functools import lru_cache

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str | None = None

    # Character library
    character_library_dir: str = "character_library"

    # Slack app
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_app_token: str = ""

    # API server
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # LLM Model Configuration
    llm_default_model: str = "claude-sonnet-4-20250514"
    llm_character_model: str | None = None
    llm_architect_model: str | None = None
    llm_editor_model: str | None = None
    llm_narrator_model: str | None = None

    # Logging
    log_format: str = "console"  # "console" | "json"

    model_config = SettingsConfigDict(env_file=".env")


def get_model_for_agent_type(agent_type: str) -> str:
    """Get the configured model for a specific agent type.

    Args:
        agent_type: One of "character", "architect", "editor", "narrator".

    Returns:
        The model name to use for this agent type.
    """
    settings = get_settings()
    agent_model_map = {
        "character": settings.llm_character_model,
        "architect": settings.llm_architect_model,
        "editor": settings.llm_editor_model,
        "narrator": settings.llm_narrator_model,
    }
    per_agent_model = agent_model_map.get(agent_type)
    return per_agent_model if per_agent_model else settings.llm_default_model


def configure_logging(log_format: str = "console"):
    """Configure structlog with stdlib logging integration."""
    # Shared processors for all logs
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    formatter = "json" if log_format == "json" else "console"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(),
                    ],
                    "foreign_pre_chain": shared_processors,
                },
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.processors.JSONRenderer(),
                    ],
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": formatter,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["stdout"],
                    "level": "INFO",
                },
                "httpx": {
                    "level": "WARNING",
                },
            },
        }
    )

    # Configure structlog to use stdlib
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def bootstrap_environment(settings: Settings) -> None:
    """Initialize environment variables from settings."""
    if settings.anthropic_api_key and "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
