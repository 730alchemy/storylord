"""Modal builders for the character creation wizard."""

from __future__ import annotations

from typing import Any


def _schema_to_input_blocks(property_schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a JSON Schema's properties to Slack input blocks.

    Each property becomes a plain_text_input block with the property's
    description as a hint and its default as the initial value.

    Args:
        property_schema: A JSON Schema object with a "properties" key.

    Returns:
        A list of input blocks, one per property, sorted by property name.
    """
    blocks = []
    properties = property_schema.get("properties", {})

    for prop_name in sorted(properties.keys()):
        prop_def = properties[prop_name]
        blocks.append(
            {
                "type": "input",
                "block_id": f"{prop_name}_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": f"{prop_name}_input",
                    "placeholder": {"type": "plain_text", "text": "0-100"},
                    "initial_value": str(prop_def.get("default", 50)),
                },
                "label": {
                    "type": "plain_text",
                    "text": prop_name.replace("_", " ").title(),
                },
                "hint": {
                    "type": "plain_text",
                    "text": prop_def.get("description", ""),
                },
            }
        )

    return blocks


# Role options shared across Modal 1 and the Correction Modal (Slice 8).
ROLE_OPTIONS: list[dict[str, Any]] = [
    {"text": {"type": "plain_text", "text": "Protagonist"}, "value": "protagonist"},
    {"text": {"type": "plain_text", "text": "Antagonist"}, "value": "antagonist"},
    {"text": {"type": "plain_text", "text": "Supporting"}, "value": "supporting"},
    {"text": {"type": "plain_text", "text": "Minor"}, "value": "minor"},
]


def build_modal_1(
    agent_types: dict[str, Any],
    channel_id: str,
) -> dict[str, Any]:
    """Build the Modal 1 (Role & Agent Config) view payload.

    Args:
        agent_types: Map of agent-type name → CharacterAgentType instance,
                     typically from discover_character_agent_types().
        channel_id: DM channel to return to after submission; stored in
                    private_metadata so the submission handler can post there.
    """
    agent_type_options = [
        {"text": {"type": "plain_text", "text": name}, "value": name}
        for name in sorted(agent_types)
    ]

    return {
        "type": "modal",
        "callback_id": "modal_1_submit",
        "title": {"type": "plain_text", "text": "Character Setup"},
        "submit": {"type": "plain_text", "text": "Next"},
        "private_metadata": channel_id,
        "blocks": [
            {
                "type": "input",
                "block_id": "role_block",
                "element": {
                    "type": "static_select",
                    "action_id": "role_select",
                    "options": ROLE_OPTIONS,
                },
                "label": {"type": "plain_text", "text": "Role"},
            },
            {
                "type": "input",
                "block_id": "agent_toggle_block",
                "element": {
                    "type": "checkboxes",
                    "action_id": "agent_toggle",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Enable agent configuration",
                            },
                            "value": "enabled",
                        }
                    ],
                },
                "label": {"type": "plain_text", "text": "Agent Configuration"},
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "agent_type_block",
                "element": {
                    "type": "static_select",
                    "action_id": "agent_type_select",
                    "options": agent_type_options,
                },
                "label": {"type": "plain_text", "text": "Agent Type"},
            },
        ],
    }
