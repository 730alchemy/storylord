"""Modal builders for the character creation wizard."""

from __future__ import annotations

from typing import Any

from slack_app.state import WizardState


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


def _schema_to_input_blocks_with_values(
    property_schema: dict[str, Any],
    current_values: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert a JSON Schema's properties to Slack input blocks with current values.

    Like _schema_to_input_blocks but uses current values instead of defaults
    from the schema. Used for the correction modal pre-population.

    Args:
        property_schema: A JSON Schema object with a "properties" key.
        current_values: Dict of property_name → current value.

    Returns:
        A list of input blocks, one per property, sorted by property name.
    """
    blocks = []
    properties = property_schema.get("properties", {})

    for prop_name in sorted(properties.keys()):
        prop_def = properties[prop_name]
        # Use current value if available, otherwise schema default
        value = current_values.get(prop_name, prop_def.get("default", 50))
        blocks.append(
            {
                "type": "input",
                "block_id": f"{prop_name}_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": f"{prop_name}_input",
                    "placeholder": {"type": "plain_text", "text": "0-100"},
                    "initial_value": str(value),
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


def build_agent_properties_modal(
    agent_type: str,
    property_schema: dict[str, Any],
    channel_id: str,
) -> dict[str, Any]:
    """Build the Agent Properties modal view payload.

    Dynamically creates number inputs for each property in the schema,
    plus a multiline text input for agent_instructions.

    Args:
        agent_type: The selected agent type name (for logging/context).
        property_schema: The JSON Schema for this agent type's properties.
        channel_id: DM channel to return to after submission.
    """
    blocks = _schema_to_input_blocks(property_schema)

    # Add agent_instructions block at the end
    blocks.append(
        {
            "type": "input",
            "block_id": "agent_instructions_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "agent_instructions_input",
                "multiline": True,
            },
            "label": {
                "type": "plain_text",
                "text": "Agent Instructions",
            },
            "hint": {
                "type": "plain_text",
                "text": "Custom behavioral instructions for this character (optional)",
            },
            "optional": True,
        }
    )

    return {
        "type": "modal",
        "callback_id": "modal_2_submit",
        "title": {"type": "plain_text", "text": "Agent Properties"},
        "submit": {"type": "plain_text", "text": "Next"},
        "private_metadata": channel_id,
        "blocks": blocks,
    }


def build_character_setup_modal(
    agent_types: dict[str, Any],
    channel_id: str,
) -> dict[str, Any]:
    """Build the Character Setup modal view payload.

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


def build_correction_modal(
    state: WizardState,
    agent_types: dict[str, Any],
    property_schema: dict[str, Any],
    channel_id: str,
) -> dict[str, Any]:
    """Build the Correction modal for editing all character fields.

    Combines all fields from the entire wizard flow into a single modal
    with values pre-populated from the current wizard state.

    All fields are always rendered (Block Kit limitation — no conditional
    visibility). Agent type, properties, and instructions fields are
    pre-populated if agent config is enabled, otherwise they show defaults
    and are ignored on submission.

    Args:
        state: Current wizard state with all collected data.
        agent_types: Map of agent-type name → CharacterAgentType instance.
        property_schema: The JSON Schema for the current agent type's properties.
        channel_id: DM channel to return to after submission.

    Returns:
        A Slack modal view payload with all fields pre-populated.
    """
    agent_type_options = [
        {"text": {"type": "plain_text", "text": name}, "value": name}
        for name in sorted(agent_types)
    ]

    # Find the currently selected role option for initial_option
    role_initial = next(
        (opt for opt in ROLE_OPTIONS if opt["value"] == state.role), ROLE_OPTIONS[0]
    )

    # Find the currently selected agent type for initial_option
    agent_type_initial = next(
        (opt for opt in agent_type_options if opt["value"] == state.agent_type),
        agent_type_options[0],
    )

    # Build checkbox initial_options for agent config
    agent_toggle_initial = (
        [
            {
                "text": {"type": "plain_text", "text": "Enable agent configuration"},
                "value": "enabled",
            }
        ]
        if state.agent_config_enabled
        else []
    )

    blocks = [
        # Freeform text fields
        {
            "type": "input",
            "block_id": "name_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "name_input",
                "initial_value": state.name,
            },
            "label": {"type": "plain_text", "text": "Name"},
        },
        {
            "type": "input",
            "block_id": "description_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "description_input",
                "multiline": True,
                "initial_value": state.description,
            },
            "label": {"type": "plain_text", "text": "Description"},
        },
        {
            "type": "input",
            "block_id": "motivations_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "motivations_input",
                "multiline": True,
                "initial_value": state.motivations,
            },
            "label": {"type": "plain_text", "text": "Motivations"},
        },
        {
            "type": "input",
            "block_id": "backstory_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "backstory_input",
                "multiline": True,
                "initial_value": state.backstory,
            },
            "label": {"type": "plain_text", "text": "Backstory"},
        },
        {
            "type": "input",
            "block_id": "relationships_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "relationships_input",
                "multiline": True,
                "initial_value": state.relationships,
            },
            "label": {"type": "plain_text", "text": "Relationships"},
        },
        # Role select (from Modal 1)
        {
            "type": "input",
            "block_id": "role_block",
            "element": {
                "type": "static_select",
                "action_id": "role_select",
                "options": ROLE_OPTIONS,
                "initial_option": role_initial,
            },
            "label": {"type": "plain_text", "text": "Role"},
        },
        # Agent config toggle (from Modal 1)
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
                "initial_options": agent_toggle_initial,
            },
            "label": {"type": "plain_text", "text": "Agent Configuration"},
            "optional": True,
        },
        # Agent type select (from Modal 1)
        {
            "type": "input",
            "block_id": "agent_type_block",
            "element": {
                "type": "static_select",
                "action_id": "agent_type_select",
                "options": agent_type_options,
                "initial_option": agent_type_initial,
            },
            "label": {"type": "plain_text", "text": "Agent Type"},
        },
    ]

    # Add agent property inputs (from Modal 2)
    # Pre-populated with current values if agent config is enabled
    blocks.extend(
        _schema_to_input_blocks_with_values(property_schema, state.agent_properties)
    )

    # Add agent_instructions block (from Modal 2)
    blocks.append(
        {
            "type": "input",
            "block_id": "agent_instructions_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "agent_instructions_input",
                "multiline": True,
                "initial_value": state.agent_instructions,
            },
            "label": {
                "type": "plain_text",
                "text": "Agent Instructions",
            },
            "hint": {
                "type": "plain_text",
                "text": "Custom behavioral instructions for this character (optional)",
            },
            "optional": True,
        }
    )

    return {
        "type": "modal",
        "callback_id": "correction_modal_submit",
        "title": {"type": "plain_text", "text": "Edit Character"},
        "submit": {"type": "plain_text", "text": "Update"},
        "private_metadata": channel_id,
        "blocks": blocks,
    }
