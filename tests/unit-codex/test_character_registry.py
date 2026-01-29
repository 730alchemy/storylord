"""Tests for agents/character/registry.py."""

from __future__ import annotations

import pytest

from agents.character.registry import CharacterRegistry
from models import CharacterMemory, CharacterProfile


class DummyAgentType:
    """Dummy agent type for testing."""

    def __init__(self) -> None:
        self.name = "dummy"
        self.create_calls: list[dict] = []

    def create_instance(
        self,
        character_id: str,
        character_profile: CharacterProfile,
        type_properties: dict,
        instructions: str,
        initial_memory: CharacterMemory | None = None,
    ):
        self.create_calls.append(
            {
                "character_id": character_id,
                "profile": character_profile,
                "properties": type_properties,
                "instructions": instructions,
                "memory": initial_memory,
            }
        )

        class DummyCharacter:
            def __init__(self, memory):
                self.memory = memory or CharacterMemory()
                self.profile = character_profile

        return DummyCharacter(initial_memory)


@pytest.fixture
def profile() -> CharacterProfile:
    return CharacterProfile(
        name="Alice",
        description="A curious adventurer",
        role="protagonist",
        motivations="Discover the truth",
        relationships="Friends with Bob",
        backstory="Grew up in a small village",
    )


@pytest.fixture
def agent_type() -> DummyAgentType:
    return DummyAgentType()


class TestCharacterRegistryCreation:
    """Tests for CharacterRegistry initialization and agent type registration."""

    def test_empty_registry(self):
        registry = CharacterRegistry()
        assert len(registry) == 0
        assert registry.list_characters() == []
        assert registry.list_agent_types() == []

    def test_registry_with_agent_types(self, agent_type: DummyAgentType):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        assert registry.list_agent_types() == ["dummy"]

    def test_register_agent_type(self, agent_type: DummyAgentType):
        registry = CharacterRegistry()
        registry.register_agent_type("custom", agent_type)
        assert "custom" in registry.list_agent_types()
        assert registry.get_agent_type("custom") == agent_type


class TestCharacterCreation:
    """Tests for creating characters in the registry."""

    def test_create_character_success(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})

        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={"trait": "curious"},
            instructions="Be adventurous",
        )

        assert registry.has_character("alice")
        assert "alice" in registry
        assert len(registry) == 1
        assert registry.list_characters() == ["alice"]

        # Verify agent type was called correctly
        assert len(agent_type.create_calls) == 1
        call = agent_type.create_calls[0]
        assert call["character_id"] == "alice"
        assert call["profile"] == profile
        assert call["properties"] == {"trait": "curious"}
        assert call["instructions"] == "Be adventurous"

    def test_create_character_with_initial_memory(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        memory = CharacterMemory()
        memory.add_interaction(event_type="spoke", content="Hello")

        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
            memory=memory,
        )

        call = agent_type.create_calls[0]
        assert call["memory"] == memory

    def test_create_character_unknown_type(self, profile: CharacterProfile):
        registry = CharacterRegistry()

        with pytest.raises(ValueError, match="Unknown character agent type"):
            registry.create_character(
                character_id="alice",
                type_name="nonexistent",
                profile=profile,
                properties={},
                instructions="",
            )

    def test_create_character_unknown_type_shows_available(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})

        with pytest.raises(ValueError, match="Available: dummy"):
            registry.create_character(
                character_id="alice",
                type_name="nonexistent",
                profile=profile,
                properties={},
                instructions="",
            )


class TestCharacterLookup:
    """Tests for looking up characters in the registry."""

    def test_get_character_success(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        created = registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
        )

        retrieved = registry.get_character("alice")
        assert retrieved == created

    def test_get_character_not_found(self):
        registry = CharacterRegistry()

        with pytest.raises(KeyError):
            registry.get_character("nonexistent")

    def test_has_character_true(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
        )

        assert registry.has_character("alice") is True

    def test_has_character_false(self):
        registry = CharacterRegistry()
        assert registry.has_character("nonexistent") is False

    def test_contains_operator(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
        )

        assert "alice" in registry
        assert "bob" not in registry


class TestMemoryManagement:
    """Tests for memory persistence and restoration."""

    def test_get_all_memories(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})

        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
        )

        memories = registry.get_all_memories()
        assert "alice" in memories
        assert isinstance(memories["alice"], CharacterMemory)

    def test_restore_memories(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
        )

        # Create memory with some data
        new_memory = CharacterMemory()
        new_memory.add_interaction(event_type="spoke", content="Restored memory")

        registry.restore_memories({"alice": new_memory})

        character = registry.get_character("alice")
        assert len(character.memory.events) == 1
        assert character.memory.events[0].content == "Restored memory"

    def test_restore_memories_skips_unknown_characters(
        self, profile: CharacterProfile, agent_type: DummyAgentType
    ):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        registry.create_character(
            character_id="alice",
            type_name="dummy",
            profile=profile,
            properties={},
            instructions="",
        )

        # This should not raise, just skip the unknown character
        memory = CharacterMemory()
        registry.restore_memories({"unknown": memory})

        # Alice's memory should be unchanged
        assert len(registry.get_character("alice").memory.events) == 0


class TestAgentTypeLookup:
    """Tests for agent type management."""

    def test_get_agent_type_success(self, agent_type: DummyAgentType):
        registry = CharacterRegistry(agent_types={"dummy": agent_type})
        assert registry.get_agent_type("dummy") == agent_type

    def test_get_agent_type_not_found(self):
        registry = CharacterRegistry()
        with pytest.raises(KeyError):
            registry.get_agent_type("nonexistent")

    def test_list_agent_types_sorted(self):
        class FakeType:
            pass

        registry = CharacterRegistry(
            agent_types={"zebra": FakeType(), "alpha": FakeType(), "beta": FakeType()}
        )
        assert registry.list_agent_types() == ["alpha", "beta", "zebra"]
