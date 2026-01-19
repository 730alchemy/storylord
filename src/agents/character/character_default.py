"""Default trait-based character agent implementation.

This module provides a character agent type based on simple personality traits
like assertiveness, warmth, formality, verbosity, and emotionality.
"""

from __future__ import annotations

from typing import Any

from agents.character.base import BaseCharacterAgent
from models import CharacterMemory, CharacterProfile


DEFAULT_PROPERTY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "assertiveness": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "How assertive and direct the character is (0=passive, 100=dominant)",
        },
        "warmth": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "How warm and friendly the character is (0=cold, 100=very warm)",
        },
        "formality": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "How formal the character's speech and manner are (0=casual, 100=very formal)",
        },
        "verbosity": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "How talkative the character is (0=terse, 100=verbose)",
        },
        "emotionality": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "default": 50,
            "description": "How openly emotional the character is (0=stoic, 100=very expressive)",
        },
    },
    "additionalProperties": False,
}


def _describe_trait(name: str, value: int) -> str:
    """Generate a description for a trait value.

    Args:
        name: The trait name.
        value: The trait value (0-100).

    Returns:
        A descriptive string for this trait level.
    """
    if value <= 20:
        level = "very low"
    elif value <= 40:
        level = "low"
    elif value <= 60:
        level = "moderate"
    elif value <= 80:
        level = "high"
    else:
        level = "very high"

    trait_descriptions = {
        "assertiveness": {
            "very low": "passive, deferential, avoids confrontation",
            "low": "generally yielding, prefers others to lead",
            "moderate": "balanced, assertive when needed but flexible",
            "high": "confident, takes initiative, speaks their mind",
            "very high": "dominant, forceful, commands attention",
        },
        "warmth": {
            "very low": "cold, distant, uncomfortable with emotional connection",
            "low": "reserved, maintains professional distance",
            "moderate": "friendly but measured, appropriate warmth",
            "high": "warm, caring, easily connects with others",
            "very high": "extremely warm, nurturing, emotionally open",
        },
        "formality": {
            "very low": "very casual, relaxed speech, ignores conventions",
            "low": "informal, uses colloquialisms freely",
            "moderate": "adapts formality to context",
            "high": "formal, proper, respects conventions",
            "very high": "very formal, precise language, highly proper",
        },
        "verbosity": {
            "very low": "terse, minimal words, gets straight to point",
            "low": "concise, economical with words",
            "moderate": "balanced, says what needs to be said",
            "high": "talkative, elaborates on points",
            "very high": "verbose, detailed, extensive explanations",
        },
        "emotionality": {
            "very low": "stoic, rarely shows emotion, controlled",
            "low": "reserved emotionally, subtle expressions",
            "moderate": "appropriate emotional expression",
            "high": "emotionally expressive, feelings evident",
            "very high": "highly emotional, wears heart on sleeve",
        },
    }

    return trait_descriptions.get(name, {}).get(level, f"{level} {name}")


def _generate_personality_description(properties: dict[str, Any]) -> str:
    """Generate a personality description from trait values.

    Args:
        properties: Dictionary of trait names to values.

    Returns:
        A formatted personality description string.
    """
    lines = ["This character's personality traits:"]

    for trait in ["assertiveness", "warmth", "formality", "verbosity", "emotionality"]:
        value = properties.get(trait, 50)
        description = _describe_trait(trait, value)
        lines.append(f"- **{trait.title()}** ({value}/100): {description}")

    return "\n".join(lines)


class DefaultCharacterAgent(BaseCharacterAgent):
    """A character agent using simple trait-based personality."""

    def __init__(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        properties: dict[str, Any],
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ):
        """Initialize the default character agent.

        Args:
            character_id: Unique identifier for this character.
            character_profile: The character's profile.
            properties: Trait values (assertiveness, warmth, etc.).
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


class DefaultCharacterAgentType:
    """Factory for creating default trait-based character agents."""

    name = "default"

    @property
    def property_schema(self) -> dict[str, Any]:
        """JSON Schema for default character agent properties.

        Returns:
            The property schema dictionary.
        """
        return DEFAULT_PROPERTY_SCHEMA

    def create_instance(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        type_properties: dict[str, Any],
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ) -> DefaultCharacterAgent:
        """Create a default character agent instance.

        Args:
            character_id: Unique identifier for this character.
            character_profile: The character's profile.
            type_properties: Trait values.
            instructions: Custom behavioral instructions.
            initial_memory: Optional existing memory to restore.

        Returns:
            A configured DefaultCharacterAgent instance.
        """
        # Apply defaults for missing traits
        properties = {
            "assertiveness": type_properties.get("assertiveness", 50),
            "warmth": type_properties.get("warmth", 50),
            "formality": type_properties.get("formality", 50),
            "verbosity": type_properties.get("verbosity", 50),
            "emotionality": type_properties.get("emotionality", 50),
        }

        return DefaultCharacterAgent(
            character_id=character_id,
            character_profile=character_profile,
            properties=properties,
            instructions=instructions,
            initial_memory=initial_memory,
        )
