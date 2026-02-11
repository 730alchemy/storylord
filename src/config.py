import logging.config
import os

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str

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

    # Console renderer with reordered columns: timestamp, level, logger, event, context vars
    default_renderer = structlog.dev.ConsoleRenderer()
    default_columns = {c.key: c for c in default_renderer._columns}
    console_columns = [
        default_columns["timestamp"],
        default_columns["level"],
        default_columns["logger"],
        default_columns["event"],
        structlog.dev.Column("", default_renderer._default_column_formatter),
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
                        structlog.dev.ConsoleRenderer(columns=console_columns),
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


def initialize_environment():
    """Initialize environment variables from settings."""
    settings = Settings()

    if "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

    return settings


# Auto-initialize when module is imported
settings = initialize_environment()
configure_logging(settings.log_format)
