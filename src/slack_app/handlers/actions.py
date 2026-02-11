"""Button action handlers for the character creation wizard."""

from __future__ import annotations

from pathlib import Path

import structlog

from agents.discovery import discover_character_agent_types, get_character_agent_type
from character_store.store import CharacterStore
from config import get_settings
from slack_app.modals import build_correction_modal
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
    settings = get_settings()
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

    # Clear wizard state (AC-27)
    state_manager.clear(user_id)
    log.info("wizard_session_cleared", user=user_id)


def handle_edit_action(
    ack,
    body: dict,
    state_manager: StateManager,
    client,
) -> None:
    """Handle Edit button click from the preview message.

    Opens the correction modal with all fields pre-populated from the
    current wizard state, allowing the user to modify any field.

    Args:
        ack: Slack ack function to acknowledge the action.
        body: The action payload from Slack.
        state_manager: The wizard state manager.
        client: Slack client for opening modals.
    """
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    state = state_manager.get(user_id)

    if state is None:
        ack()
        log.warning("edit_action_no_state", user=user_id)
        client.chat_postMessage(
            channel=channel_id,
            text="No active character session. Use `/create-character` to start.",
        )
        return

    ack()

    # Discover agent types and get property schema for current agent type
    agent_types = discover_character_agent_types()
    agent_type_instance = get_character_agent_type(state.agent_type)
    property_schema = agent_type_instance.property_schema

    # Open correction modal with all fields pre-populated
    client.views_open(
        trigger_id=body["trigger_id"],
        view=build_correction_modal(
            state=state,
            agent_types=agent_types,
            property_schema=property_schema,
            channel_id=channel_id,
        ),
    )

    log.info("correction_modal_opened", user=user_id)
