"""Modal submission handlers for the character creation wizard."""

from __future__ import annotations

import structlog

from slack_app.state import StateManager, WizardPhase

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
        # Slice 7 will render the preview here.
        client.chat_postMessage(
            channel=channel_id,
            text="Role saved! Preparing your character preview...",
        )
