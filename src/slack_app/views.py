"""Message builders for preview and confirmation in the wizard flow."""

from __future__ import annotations

from pathlib import Path

import yaml

from slack_app.state import WizardState


def build_preview_message(state: WizardState) -> dict:
    """Build the preview message showing the assembled CharacterProfile.

    Converts the wizard state to a CharacterProfile and displays it as a
    YAML code block with Save and Edit action buttons.

    Args:
        state: The current wizard state containing all collected data.

    Returns:
        A Slack message dict with text, blocks, and action buttons.
    """
    profile = state.to_character_profile()
    yaml_data = profile.model_dump(mode="json", exclude_none=True)
    yaml_str = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

    return {
        "text": "Here's your character preview:",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Here's your character preview:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```yaml\n{yaml_str}\n```",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Save"},
                        "action_id": "save_character",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Edit"},
                        "action_id": "edit_character",
                    },
                ],
            },
        ],
    }


def build_confirmation_message(file_path: Path) -> dict:
    """Build the confirmation message after successful save.

    Args:
        file_path: The path where the character YAML was saved.

    Returns:
        A Slack message dict confirming the save with file path.
    """
    return {
        "text": f"Character saved to {file_path}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ Character saved to `{file_path}`",
                },
            }
        ],
    }
