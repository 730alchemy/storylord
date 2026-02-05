"""Modal submission handlers for the character creation wizard."""

from __future__ import annotations

import structlog

from agents.discovery import get_character_agent_type
from slack_app.state import StateManager, WizardPhase
from slack_app.views import build_preview_message

log = structlog.get_logger(__name__)


def handle_modal_1_submit(
    ack,
    view: dict,
    body: dict,
    state_manager: StateManager,
    client,
) -> None:
    """Handle Modal 1 (Role & Agent Config) submission.

    Toggle off  → state advances to PREVIEW; agent_config stays None.
    Toggle on   → state advances to MODAL_2_OPEN with selected agent_type stored.

    A follow-up message is posted to the DM channel (stored in
    private_metadata) so the user knows what happens next.  Slice 6 will
    replace the MODAL_2_OPEN message with a Modal 2 opener; Slice 7 will
    replace the PREVIEW message with the actual character preview.
    """
    user_id = body["user"]["id"]
    channel_id = view["private_metadata"]
    state = state_manager.get(user_id)

    if state is None:
        ack()
        return

    values = view["state"]["values"]
    state.role = values["role_block"]["role_select"]["selected_option"]["value"]

    toggle_options = values["agent_toggle_block"]["agent_toggle"]["selected_options"]
    state.agent_config_enabled = any(
        opt["value"] == "enabled" for opt in toggle_options
    )

    if state.agent_config_enabled:
        state.agent_type = values["agent_type_block"]["agent_type_select"][
            "selected_option"
        ]["value"]
        state.phase = WizardPhase.MODAL_2_OPEN
        log.info(
            "modal_1_submitted",
            user=user_id,
            role=state.role,
            agent_type=state.agent_type,
            next_phase="MODAL_2_OPEN",
        )
        ack()
        # Post a button to open Modal 2
        client.chat_postMessage(
            channel=channel_id,
            text="Now let's configure the agent properties.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Now let's configure the agent properties.",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Continue"},
                            "action_id": "open_modal_2",
                        }
                    ],
                },
            ],
        )
    else:
        state.phase = WizardPhase.PREVIEW
        log.info(
            "modal_1_submitted",
            user=user_id,
            role=state.role,
            agent_config_enabled=False,
            next_phase="PREVIEW",
        )
        ack()
        # Render the character preview with Save/Edit buttons
        client.chat_postMessage(
            channel=channel_id,
            **build_preview_message(state),
        )


def handle_modal_2_submit(
    ack,
    view: dict,
    body: dict,
    state_manager: StateManager,
    client,
) -> None:
    """Handle Modal 2 (Agent Properties) submission.

    Extracts numeric property values and agent_instructions, stores them
    in state, and advances to PREVIEW. Validation is added in commit 4.
    """
    user_id = body["user"]["id"]
    channel_id = view["private_metadata"]
    state = state_manager.get(user_id)

    if state is None:
        ack()
        return

    values = view["state"]["values"]

    # Get agent type schema to know which properties to expect
    agent_type_instance = get_character_agent_type(state.agent_type)
    property_schema = agent_type_instance.property_schema
    properties = property_schema.get("properties", {})

    # Extract and validate numeric properties (AC-20)
    agent_properties = {}
    errors = {}

    for prop_name in properties:
        block_id = f"{prop_name}_block"
        action_id = f"{prop_name}_input"
        value_str = values[block_id][action_id]["value"]

        try:
            value = float(value_str)
            if value < 0 or value > 100:
                errors[block_id] = "Must be between 0 and 100"
            else:
                agent_properties[prop_name] = value
        except (ValueError, TypeError):
            errors[block_id] = "Must be a number"

    if errors:
        ack(response_action="errors", errors=errors)
        return

    # Extract agent_instructions (optional)
    instructions_value = values["agent_instructions_block"][
        "agent_instructions_input"
    ].get("value")
    agent_instructions = instructions_value or ""

    # Store in state and advance to PREVIEW
    state.agent_properties = agent_properties
    state.agent_instructions = agent_instructions
    state.phase = WizardPhase.PREVIEW

    log.info(
        "modal_2_submitted",
        user=user_id,
        agent_type=state.agent_type,
        properties=agent_properties,
        next_phase="PREVIEW",
    )

    ack()
    # Render the character preview with Save/Edit buttons
    client.chat_postMessage(
        channel=channel_id,
        **build_preview_message(state),
    )


def handle_correction_modal_submit(
    ack,
    view: dict,
    body: dict,
    state_manager: StateManager,
    client,
) -> None:
    """Handle Correction modal submission.

    Extracts all field values, updates the wizard state, validates agent
    properties if enabled, and re-renders the preview with updated values.
    State remains PREVIEW (AC-25).

    Args:
        ack: Slack ack function.
        view: The view payload from Slack.
        body: The submission body.
        state_manager: The wizard state manager.
        client: Slack client for posting messages.
    """
    user_id = body["user"]["id"]
    channel_id = view["private_metadata"]
    state = state_manager.get(user_id)

    if state is None:
        ack()
        return

    values = view["state"]["values"]

    # Extract freeform text fields
    state.name = values["name_block"]["name_input"]["value"]
    state.description = values["description_block"]["description_input"]["value"]
    state.motivations = values["motivations_block"]["motivations_input"]["value"]
    state.backstory = values["backstory_block"]["backstory_input"]["value"]
    state.relationships = values["relationships_block"]["relationships_input"]["value"]

    # Extract role
    state.role = values["role_block"]["role_select"]["selected_option"]["value"]

    # Extract agent config toggle
    toggle_options = values["agent_toggle_block"]["agent_toggle"]["selected_options"]
    state.agent_config_enabled = any(
        opt["value"] == "enabled" for opt in toggle_options
    )

    # Extract agent type
    state.agent_type = values["agent_type_block"]["agent_type_select"][
        "selected_option"
    ]["value"]

    # If agent config is enabled, extract and validate properties
    if state.agent_config_enabled:
        agent_type_instance = get_character_agent_type(state.agent_type)
        property_schema = agent_type_instance.property_schema
        properties = property_schema.get("properties", {})

        agent_properties = {}
        errors = {}

        for prop_name in properties:
            block_id = f"{prop_name}_block"
            action_id = f"{prop_name}_input"
            value_str = values[block_id][action_id]["value"]

            try:
                value = float(value_str)
                if value < 0 or value > 100:
                    errors[block_id] = "Must be between 0 and 100"
                else:
                    agent_properties[prop_name] = value
            except (ValueError, TypeError):
                errors[block_id] = "Must be a number"

        if errors:
            ack(response_action="errors", errors=errors)
            return

        # Extract agent_instructions
        instructions_value = values["agent_instructions_block"][
            "agent_instructions_input"
        ].get("value")
        state.agent_instructions = instructions_value or ""
        state.agent_properties = agent_properties
    else:
        # Clear agent config if disabled
        state.agent_properties = {}
        state.agent_instructions = ""

    # State remains PREVIEW (AC-25)
    log.info(
        "correction_modal_submitted",
        user=user_id,
        changes_applied=True,
    )

    ack()
    # Re-render the preview with updated values
    client.chat_postMessage(
        channel=channel_id,
        **build_preview_message(state),
    )
