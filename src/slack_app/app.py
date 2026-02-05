"""Bolt app setup and event/command registration."""

from __future__ import annotations

from slack_bolt import App

from config import settings
from slack_app.handlers.commands import handle_create_character
from slack_app.state import StateManager

# Shared state manager — one instance for the lifetime of the process
state_manager = StateManager()


def create_app() -> App:
    """Create and configure the Bolt App with all registered handlers."""
    app = App(
        signing_secret=settings.slack_signing_secret,
        token=settings.slack_bot_token,
    )

    @app.command("/create-character")
    def create_character(ack, command):
        handle_create_character(
            ack=ack,
            command=command,
            state_manager=state_manager,
        )

    return app
