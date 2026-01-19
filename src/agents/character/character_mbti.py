"""MBTI-based character agent implementation.

This module provides a character agent type based on Myers-Briggs Type Indicator
personality dimensions: Extroversion/Introversion, Intuition/Sensing,
Thinking/Feeling, and Judging/Perceiving.
"""

from __future__ import annotations

from typing import Any

from agents.character.base import BaseCharacterAgent
from models import CharacterMemory, CharacterProfile


MBTI_PROPERTY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "extroversion": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "E/I dimension: 0=Introverted, 100=Extroverted",
        },
        "intuition": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "N/S dimension: 0=Sensing, 100=Intuitive",
        },
        "thinking": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "T/F dimension: 0=Feeling, 100=Thinking",
        },
        "judging": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "J/P dimension: 0=Perceiving, 100=Judging",
        },
    },
    "additionalProperties": False,
}


def _get_mbti_type(properties: dict[str, Any]) -> str:
    """Derive the 4-letter MBTI type from property values.

    Args:
        properties: Dictionary of MBTI dimension values.

    Returns:
        A 4-letter MBTI type string (e.g., "INTJ").
    """
    e_i = "E" if properties.get("extroversion", 50) >= 50 else "I"
    n_s = "N" if properties.get("intuition", 50) >= 50 else "S"
    t_f = "T" if properties.get("thinking", 50) >= 50 else "F"
    j_p = "J" if properties.get("judging", 50) >= 50 else "P"
    return f"{e_i}{n_s}{t_f}{j_p}"


def _describe_ei_dimension(value: int) -> str:
    """Describe the Extroversion/Introversion dimension.

    Args:
        value: The dimension value (0-100).

    Returns:
        A description of how this dimension manifests.
    """
    if value <= 25:
        return "Strongly introverted - deeply reflective, needs extensive alone time to recharge, prefers one-on-one interactions, thinks before speaking"
    elif value <= 45:
        return "Introverted - prefers smaller groups, values depth over breadth in relationships, processes internally before expressing"
    elif value <= 55:
        return "Balanced on the E/I spectrum - can adapt to both social and solitary situations, flexible in energy management"
    elif value <= 75:
        return "Extroverted - energized by social interaction, thinks out loud, comfortable in groups, seeks external stimulation"
    else:
        return "Strongly extroverted - thrives in social settings, very outgoing, processes through conversation, may struggle with extended solitude"


def _describe_ns_dimension(value: int) -> str:
    """Describe the Intuition/Sensing dimension.

    Args:
        value: The dimension value (0-100).

    Returns:
        A description of how this dimension manifests.
    """
    if value <= 25:
        return "Strongly sensing - focuses on concrete facts and present reality, trusts experience over theory, practical and detail-oriented"
    elif value <= 45:
        return "Sensing preference - values tangible evidence, prefers proven methods, attentive to sensory details"
    elif value <= 55:
        return "Balanced on the N/S spectrum - can appreciate both big picture and details, flexible in information gathering"
    elif value <= 75:
        return "Intuitive - focuses on patterns and possibilities, interested in meaning and future potential, comfortable with abstract concepts"
    else:
        return "Strongly intuitive - sees connections others miss, drawn to theory and innovation, may overlook practical details"


def _describe_tf_dimension(value: int) -> str:
    """Describe the Thinking/Feeling dimension.

    Args:
        value: The dimension value (0-100).

    Returns:
        A description of how this dimension manifests.
    """
    if value <= 25:
        return "Strongly feeling - makes decisions based on values and impact on people, empathetic, seeks harmony, may prioritize relationships over logic"
    elif value <= 45:
        return "Feeling preference - considers emotional impact, values-driven, diplomatic, strives for consensus"
    elif value <= 55:
        return "Balanced on the T/F spectrum - can employ both logic and empathy, context-dependent decision making"
    elif value <= 75:
        return "Thinking preference - logical decision-making, values fairness and consistency, comfortable with objective critique"
    else:
        return "Strongly thinking - highly analytical, prioritizes logic over emotions, may seem detached or blunt"


def _describe_jp_dimension(value: int) -> str:
    """Describe the Judging/Perceiving dimension.

    Args:
        value: The dimension value (0-100).

    Returns:
        A description of how this dimension manifests.
    """
    if value <= 25:
        return "Strongly perceiving - highly spontaneous and adaptable, dislikes rigid plans, keeps options open, may procrastinate on decisions"
    elif value <= 45:
        return "Perceiving preference - flexible approach, comfortable with ambiguity, responsive to new information"
    elif value <= 55:
        return "Balanced on the J/P spectrum - can be both structured and flexible depending on situation"
    elif value <= 75:
        return "Judging preference - prefers structure and plans, decisive, goal-oriented, likes closure"
    else:
        return "Strongly judging - highly organized and methodical, uncomfortable with uncertainty, prefers clear schedules and decisions"


def _generate_personality_description(properties: dict[str, Any]) -> str:
    """Generate a personality description from MBTI values.

    Args:
        properties: Dictionary of MBTI dimension values.

    Returns:
        A formatted personality description string.
    """
    mbti_type = _get_mbti_type(properties)

    lines = [
        f"This character has an **{mbti_type}** personality type based on their MBTI dimensions:",
        "",
        f"**Extroversion/Introversion** ({properties.get('extroversion', 50)}/100):",
        _describe_ei_dimension(properties.get("extroversion", 50)),
        "",
        f"**Intuition/Sensing** ({properties.get('intuition', 50)}/100):",
        _describe_ns_dimension(properties.get("intuition", 50)),
        "",
        f"**Thinking/Feeling** ({properties.get('thinking', 50)}/100):",
        _describe_tf_dimension(properties.get("thinking", 50)),
        "",
        f"**Judging/Perceiving** ({properties.get('judging', 50)}/100):",
        _describe_jp_dimension(properties.get("judging", 50)),
    ]

    return "\n".join(lines)


class MBTICharacterAgent(BaseCharacterAgent):
    """A character agent using MBTI-based personality."""

    def __init__(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        properties: dict[str, Any],
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ):
        """Initialize the MBTI character agent.

        Args:
            character_id: Unique identifier for this character.
            character_profile: The character's profile.
            properties: MBTI dimension values.
            instructions: Custom behavioral instructions.
            initial_memory: Optional existing memory to restore.
        """
        personality_description = _generate_personality_description(properties)

        super().__init__(
            character_id=character_id,
            character_profile=character_profile,
            personality_description=personality_description,
            instructions=instructions,
            initial_memory=initial_memory,
        )

        self.properties = properties
        self.mbti_type = _get_mbti_type(properties)


class MBTICharacterAgentType:
    """Factory for creating MBTI-based character agents."""

    name = "mbti"

    @property
    def property_schema(self) -> dict[str, Any]:
        """JSON Schema for MBTI character agent properties.

        Returns:
            The property schema dictionary.
        """
        return MBTI_PROPERTY_SCHEMA

    def create_instance(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        type_properties: dict[str, Any],
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ) -> MBTICharacterAgent:
        """Create an MBTI character agent instance.

        Args:
            character_id: Unique identifier for this character.
            character_profile: The character's profile.
            type_properties: MBTI dimension values.
            instructions: Custom behavioral instructions.
            initial_memory: Optional existing memory to restore.

        Returns:
            A configured MBTICharacterAgent instance.
        """
        # Apply defaults for missing dimensions
        properties = {
            "extroversion": type_properties.get("extroversion", 50),
            "intuition": type_properties.get("intuition", 50),
            "thinking": type_properties.get("thinking", 50),
            "judging": type_properties.get("judging", 50),
        }

        return MBTICharacterAgent(
            character_id=character_id,
            character_profile=character_profile,
            properties=properties,
            instructions=instructions,
            initial_memory=initial_memory,
        )
