"""Protocol definitions for character agents.

Character agents embody individual story characters with personality-driven
dialogue, thoughts, decisions, and the ability to answer questions from
other agents.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from models import CharacterMemory, CharacterProfile
from tools.registry import ToolRegistry


class SpeakInput(BaseModel):
    """Input for the speak method - generating dialogue."""

    scene_context: str
    conversation_history: list[str] = []
    prompt: str


class ThinkInput(BaseModel):
    """Input for the think method - internal thoughts."""

    scene_context: str
    situation: str


class ChooseInput(BaseModel):
    """Input for the choose method - making decisions."""

    scene_context: str
    choices: list[str]
    context: str


class AnswerInput(BaseModel):
    """Input for the answer method - answering questions from other agents."""

    question: str
    asking_agent: str
    context: str = ""


class CharacterResponse(BaseModel):
    """Response from a character agent method."""

    content: str
    emotional_state: str = "neutral"
    internal_notes: str = ""


class CharacterAgentType(Protocol):
    """Factory protocol for creating character agent instances.

    CharacterAgentType implementations are discovered via entry points and
    provide type-specific schemas and instance creation.
    """

    name: str

    @property
    def property_schema(self) -> dict[str, Any]:
        """JSON Schema for type-specific properties.

        Returns:
            A dictionary defining the expected properties and their types
            for this character agent type.
        """
        ...

    def create_instance(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        type_properties: dict[str, Any],
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ) -> CharacterAgent:
        """Create a configured character agent instance.

        Args:
            character_id: Unique identifier for this character.
            character_profile: The character's profile (name, description, etc.).
            type_properties: Type-specific configuration (e.g., MBTI scores).
            instructions: Custom behavioral instructions for this character.
            initial_memory: Optional existing memory to restore.

        Returns:
            A configured CharacterAgent instance.
        """
        ...


class CharacterAgent(Protocol):
    """Protocol for a configured character agent instance with memory.

    CharacterAgent instances maintain memory across scenes and can speak,
    think, make choices, and answer questions in character.
    """

    character_id: str
    memory: CharacterMemory

    def speak(
        self,
        input: SpeakInput,
        tools: ToolRegistry | None = None,
    ) -> CharacterResponse:
        """Generate dialogue in character.

        Args:
            input: The speaking context and prompt.
            tools: Optional registry of tools the agent can use.

        Returns:
            The character's dialogue response.
        """
        ...

    def think(
        self,
        input: ThinkInput,
        tools: ToolRegistry | None = None,
    ) -> CharacterResponse:
        """Generate internal thoughts in character.

        Args:
            input: The thinking context and situation.
            tools: Optional registry of tools the agent can use.

        Returns:
            The character's internal thoughts.
        """
        ...

    def choose(
        self,
        input: ChooseInput,
        tools: ToolRegistry | None = None,
    ) -> CharacterResponse:
        """Make a decision in character.

        Args:
            input: The choice context and available options.
            tools: Optional registry of tools the agent can use.

        Returns:
            The character's decision and reasoning.
        """
        ...

    def answer(
        self,
        input: AnswerInput,
        tools: ToolRegistry | None = None,
    ) -> CharacterResponse:
        """Answer a question from another agent.

        Args:
            input: The question and context.
            tools: Optional registry of tools the agent can use.

        Returns:
            The character's answer.
        """
        ...
