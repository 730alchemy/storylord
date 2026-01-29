"""Shared test fixtures for unit-codex tests."""

from __future__ import annotations

from typing import Any

import pytest

from models import (
    CharacterAgentConfig,
    CharacterMemory,
    CharacterProfile,
    StoryInput,
)


# =============================================================================
# Dummy/Mock Classes
# =============================================================================


class DummyLLM:
    """Dummy LLM that can be used to replace ChatAnthropic in tests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.model = kwargs.get("model")
        self.args = args
        self.kwargs = kwargs

    def with_structured_output(self, *_args: Any, **_kwargs: Any) -> "DummyLLM":
        return self

    def bind_tools(self, *_args: Any, **_kwargs: Any) -> "DummyLLM":
        return self

    def invoke(self, *_args: Any, **_kwargs: Any) -> Any:
        return None


class DummyCharacter:
    """Dummy character agent for testing."""

    def __init__(self, memory: CharacterMemory | None = None) -> None:
        self.memory = memory or CharacterMemory()

    def speak(self, speak_input: Any) -> Any:
        from agents.character.protocols import CharacterResponse

        return CharacterResponse(content="Hello", emotional_state="neutral")


class DummyCharacterRegistry:
    """Dummy character registry for testing."""

    def __init__(self) -> None:
        self.characters: dict[str, DummyCharacter] = {}

    def has_character(self, character_id: str) -> bool:
        return character_id in self.characters

    def get_character(self, character_id: str) -> DummyCharacter:
        if character_id not in self.characters:
            raise KeyError(f"Unknown character: {character_id}")
        return self.characters[character_id]

    def add_character(self, character_id: str, character: DummyCharacter) -> None:
        self.characters[character_id] = character


class DummyToolRegistry:
    """Dummy tool registry for testing."""

    def __init__(self, tool_names: list[str] | None = None) -> None:
        self.tool_names = tool_names or []
        self.configured = False
        self.context: Any = None

    def configure(self, context: Any) -> None:
        self.configured = True
        self.context = context

    def execute(self, name: str, **params: Any) -> Any:
        return {"ok": params}

    def list_tools(self) -> list[dict]:
        return [{"name": name} for name in self.tool_names]

    def __contains__(self, name: str) -> bool:
        return name in self.tool_names

    def __len__(self) -> int:
        return len(self.tool_names)


class DummyAgentType:
    """Dummy character agent type for testing."""

    def __init__(self, name: str = "dummy") -> None:
        self.name = name

    def create_instance(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        type_properties: dict,
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ) -> DummyCharacter:
        return DummyCharacter(memory=initial_memory)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def character_profile() -> CharacterProfile:
    """Create a basic character profile for testing."""
    return CharacterProfile(
        name="Test",
        description="A test character",
        role="protagonist",
        motivations="Testing motivation",
        relationships="None",
        backstory="Test backstory",
    )


@pytest.fixture
def character_profile_with_agent() -> CharacterProfile:
    """Create a character profile with agent configuration."""
    return CharacterProfile(
        name="TestAgent",
        description="A test character with agent",
        role="protagonist",
        motivations="Testing motivation",
        relationships="None",
        backstory="Test backstory",
        agent_config=CharacterAgentConfig(agent_type="default"),
    )


@pytest.fixture
def story_input(character_profile: CharacterProfile) -> StoryInput:
    """Create a basic story input for testing."""
    return StoryInput(
        story_idea="Test idea",
        characters=[character_profile],
        num_plot_events=1,
        beats_per_event=(1, 1),
        tone="neutral",
        output_file="test_output",
    )


@pytest.fixture
def story_input_with_agent(
    character_profile_with_agent: CharacterProfile,
) -> StoryInput:
    """Create a story input with character agent configuration."""
    return StoryInput(
        story_idea="Test idea",
        characters=[character_profile_with_agent],
        num_plot_events=1,
        beats_per_event=(1, 1),
        tone="neutral",
        output_file="test_output",
    )


@pytest.fixture
def character_memory() -> CharacterMemory:
    """Create an empty character memory for testing."""
    return CharacterMemory()


@pytest.fixture
def populated_memory() -> CharacterMemory:
    """Create a character memory with some data."""
    memory = CharacterMemory()
    memory.add_interaction(
        event_type="spoke",
        content="Hello there",
        scene_reference="scene-1",
        emotional_state="happy",
    )
    memory.add_knowledge("Secret passage exists")
    memory.update_relationship("Alice", sentiment="positive", trust_delta=0.2)
    return memory
