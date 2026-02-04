"""Slash command handlers for the Slack character creation app."""

from __future__ import annotations

from typing import Callable

from slack_app.state import StateManager


def handle_create_character(
    ack: Callable,
    say: Callable,
    command: dict,
    state_manager: StateManager,
) -> None:
    """Handle the /create-character slash command.

    Discards any existing wizard session for this user, starts a new
    one at WAITING_NAME, and asks for the character's name.

    Args:
        ack: Bolt ack callable — must be called to acknowledge the command.
        say: Bolt say callable — posts a message in the channel.
        command: The parsed slash command payload (contains user_id).
        state_manager: Shared StateManager instance.
    """
    ack()
    state_manager.start_new(command["user_id"])
    say(text="Let's create a character. What's their name?")
