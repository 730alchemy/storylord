"""Runtime character registry for managing character agent instances.

This module provides the CharacterRegistry class that manages character agent
instances, their creation, and memory persistence across scenes.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel

from agents.character.protocols import CharacterAgent, CharacterAgentType
from models import CharacterMemory, CharacterProfile

log = structlog.get_logger(__name__)


class CharacterRegistry(BaseModel):
    """Runtime registry managing character agent instances.

    The registry handles character agent creation, caching, and memory
    persistence across scenes in a story generation session.
    """

    def __init__(self, agent_types: dict[str, "CharacterAgentType"] | None = None):
        """Initialize the registry.

        Args:
            agent_types: Dictionary of available agent types. If None,
                         types will be discovered via entry points.
        """
        self._agent_types = agent_types or {}
        self._characters: dict[str, CharacterAgent] = {}

    def register_agent_type(
        self,
        name: str,
        agent_type: CharacterAgentType,
    ) -> None:
        """Register a character agent type.

        Args:
            name: The name to register the type under.
            agent_type: The agent type to register.
        """
        self._agent_types[name] = agent_type
        log.debug("character_agent_type_registered", type_name=name)

    def create_character(
        self,
        character_id: str,
        type_name: str,
        profile: CharacterProfile,
        properties: dict[str, Any],
        instructions: str,
        memory: CharacterMemory | None = None,
    ) -> CharacterAgent:
        """Create and register a character agent instance.

        Args:
            character_id: Unique identifier for this character.
            type_name: Name of the agent type to use.
            profile: The character's profile.
            properties: Type-specific configuration properties.
            instructions: Custom behavioral instructions.
            memory: Optional existing memory to restore.

        Returns:
            The created character agent instance.

        Raises:
            ValueError: If the specified agent type is not found.
        """
        if type_name not in self._agent_types:
            available = ", ".join(sorted(self._agent_types.keys())) or "(none)"
            raise ValueError(
                f"Unknown character agent type '{type_name}'. Available: {available}"
            )

        agent_type = self._agent_types[type_name]
        character = agent_type.create_instance(
            character_id=character_id,
            character_profile=profile,
            type_properties=properties,
            instructions=instructions,
            initial_memory=memory,
        )

        self._characters[character_id] = character
        log.info(
            "character_created",
            character_id=character_id,
            type_name=type_name,
            has_prior_memory=memory is not None,
        )

        return character

    def get_character(self, character_id: str) -> CharacterAgent:
        """Get a character agent by ID.

        Args:
            character_id: The character's unique identifier.

        Returns:
            The character agent instance.

        Raises:
            KeyError: If the character is not found.
        """
        return self._characters[character_id]

    def has_character(self, character_id: str) -> bool:
        """Check if a character exists in the registry.

        Args:
            character_id: The character's unique identifier.

        Returns:
            True if the character exists, False otherwise.
        """
        return character_id in self._characters

    def list_characters(self) -> list[str]:
        """List all registered character IDs.

        Returns:
            A list of character IDs.
        """
        return list(self._characters.keys())

    def get_all_memories(self) -> dict[str, CharacterMemory]:
        """Get all character memories for persistence.

        Returns:
            A dictionary mapping character IDs to their memories.
        """
        return {char_id: char.memory for char_id, char in self._characters.items()}

    def restore_memories(
        self,
        memories: dict[str, CharacterMemory],
    ) -> None:
        """Restore character memories from persistence.

        This is used when resuming a story generation session. Characters
        must already be created in the registry before calling this method.

        Args:
            memories: Dictionary mapping character IDs to memories.

        Raises:
            KeyError: If a character ID in memories doesn't exist.
        """
        for char_id, memory in memories.items():
            if char_id in self._characters:
                # Replace the character's memory with the restored one
                self._characters[char_id].memory = memory
                log.debug("memory_restored", character_id=char_id)
            else:
                log.warning(
                    "memory_restore_skipped",
                    character_id=char_id,
                    reason="character not found",
                )

    def list_agent_types(self) -> list[str]:
        """List all available agent type names.

        Returns:
            A sorted list of agent type names.
        """
        return sorted(self._agent_types.keys())

    def get_agent_type(self, name: str) -> CharacterAgentType:
        """Get an agent type by name.

        Args:
            name: The agent type name.

        Returns:
            The agent type.

        Raises:
            KeyError: If the agent type is not found.
        """
        return self._agent_types[name]

    def __len__(self) -> int:
        """Return the number of characters in the registry."""
        return len(self._characters)

    def __contains__(self, character_id: str) -> bool:
        """Check if a character is in the registry."""
        return character_id in self._characters
