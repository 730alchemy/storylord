"""Slash command handlers for the Slack character creation app."""

from __future__ import annotations

from typing import Callable

from slack_app.state import StateManager


def handle_create_character(
    ack: Callable,
    command: dict,
    state_manager: StateManager,
) -> None:
    """Handle the /create-character slash command.

    Discards any existing wizard session for this user, starts a new
    one at WAITING_NAME, and responds ephemerally asking for the
    character's name. The ephemeral response requires no scope beyond
    the auto-granted 'commands'.

    Args:
        ack: Bolt ack callable — must be called to acknowledge the command.
            Passing text makes the response ephemeral (visible only to
            the user who invoked the command).
        command: The parsed slash command payload (contains user_id).
        state_manager: Shared StateManager instance.
    """
    state_manager.start_new(command["user_id"])
    ack(text="Let's create a character! DM me with their name to get started.")
