"""Button action handlers for the character creation wizard."""

from __future__ import annotations

from pathlib import Path

import structlog

from character_store.store import CharacterStore
from config import settings
from slack_app.state import StateManager
from slack_app.views import build_confirmation_message

log = structlog.get_logger(__name__)


def handle_save_action(
    ack,
    body: dict,
    state_manager: StateManager,
    client,
) -> None:
    """Handle Save button click from the preview message.

    Converts the wizard state to a CharacterProfile, saves it via
    CharacterStore, and posts a confirmation with the file path.

    Args:
        ack: Slack ack function to acknowledge the action.
        body: The action payload from Slack.
        state_manager: The wizard state manager.
        client: Slack client for posting messages.
    """
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    state = state_manager.get(user_id)

    if state is None:
        ack()
        log.warning("save_action_no_state", user=user_id)
        client.chat_postMessage(
            channel=channel_id,
            text="No active character session. Use `/create-character` to start.",
        )
        return

    ack()

    # Convert state to profile and save
    profile = state.to_character_profile()
    store = CharacterStore(library_dir=Path(settings.character_library_dir))
    saved_path = store.save(profile)

    log.info(
        "character_saved",
        user=user_id,
        character_name=profile.name,
        file_path=str(saved_path),
    )

    # Post confirmation
    client.chat_postMessage(
        channel=channel_id,
        **build_confirmation_message(saved_path),
    )
