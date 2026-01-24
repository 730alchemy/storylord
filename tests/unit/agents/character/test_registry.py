"""Unit tests for CharacterRegistry class."""

from unittest.mock import MagicMock, patch

import pytest

from agents.character.registry import CharacterRegistry
from models import CharacterMemory, CharacterProfile


@pytest.fixture
def sample_profile() -> CharacterProfile:
    """A sample character profile for testing."""
    return CharacterProfile(
        name="Test Character",
        description="A test character",
        role="protagonist",
        motivations="Testing",
        relationships="None",
        backstory="Created for testing",
    )


@pytest.fixture
def mock_agent_type():
    """Create a mock agent type."""
    mock_type = MagicMock()
    mock_type.name = "mock"
    mock_type.property_schema = {"type": "object", "properties": {}}

    def create_instance(**kwargs):
        mock_agent = MagicMock()
        mock_agent.memory = kwargs.get("initial_memory") or CharacterMemory()
        return mock_agent

    mock_type.create_instance = MagicMock(side_effect=create_instance)
    return mock_type


class TestCharacterRegistryInit:
    """Tests for CharacterRegistry initialization."""

    def test_init_empty(self):
        """Empty registry can be created."""
        registry = CharacterRegistry()

        assert len(registry) == 0
        assert registry.list_agent_types() == []

    def test_init_with_agent_types(self, mock_agent_type):
        """Registry can be initialized with agent types."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        assert "mock" in registry.list_agent_types()


class TestCharacterRegistryRegisterAgentType:
    """Tests for CharacterRegistry.register_agent_type() method."""

    def test_register_agent_type(self, mock_agent_type):
        """Agent type is registered successfully."""
        registry = CharacterRegistry()

        registry.register_agent_type("custom", mock_agent_type)

        assert "custom" in registry.list_agent_types()


class TestCharacterRegistryCreateCharacter:
    """Tests for CharacterRegistry.create_character() method."""

    def test_create_character_success(self, mock_agent_type, sample_profile):
        """Character is created and stored in registry."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        character = registry.create_character(
            character_id="char_1",
            type_name="mock",
            profile=sample_profile,
            properties={},
            instructions="Be nice",
        )

        assert character is not None
        assert registry.has_character("char_1")
        assert len(registry) == 1

    def test_create_character_unknown_type_raises_valueerror(self, sample_profile):
        """ValueError raised for unknown agent type."""
        registry = CharacterRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.create_character(
                character_id="char_1",
                type_name="unknown",
                profile=sample_profile,
                properties={},
                instructions="",
            )

        assert "Unknown character agent type 'unknown'" in str(exc_info.value)

    def test_create_character_error_message_lists_available_types(
        self, mock_agent_type, sample_profile
    ):
        """Error message lists available agent types."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        with pytest.raises(ValueError) as exc_info:
            registry.create_character(
                character_id="char_1",
                type_name="nonexistent",
                profile=sample_profile,
                properties={},
                instructions="",
            )

        assert "Available: mock" in str(exc_info.value)

    def test_create_character_error_message_when_no_types_available(
        self, sample_profile
    ):
        """Error message shows (none) when no types available."""
        registry = CharacterRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.create_character(
                character_id="char_1",
                type_name="any",
                profile=sample_profile,
                properties={},
                instructions="",
            )

        assert "Available: (none)" in str(exc_info.value)

    def test_create_character_passes_properties(self, mock_agent_type, sample_profile):
        """Properties are passed to agent type create_instance."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        registry.create_character(
            character_id="char_1",
            type_name="mock",
            profile=sample_profile,
            properties={"key": "value"},
            instructions="Do stuff",
        )

        mock_agent_type.create_instance.assert_called_once()
        call_kwargs = mock_agent_type.create_instance.call_args[1]
        assert call_kwargs["type_properties"] == {"key": "value"}
        assert call_kwargs["instructions"] == "Do stuff"

    def test_create_character_with_initial_memory(
        self, mock_agent_type, sample_profile
    ):
        """Initial memory is passed through to agent type."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        memory = CharacterMemory()
        memory.add_knowledge(fact="Existing fact")

        registry.create_character(
            character_id="char_1",
            type_name="mock",
            profile=sample_profile,
            properties={},
            instructions="",
            memory=memory,
        )

        call_kwargs = mock_agent_type.create_instance.call_args[1]
        assert call_kwargs["initial_memory"] is memory


class TestCharacterRegistryGetCharacter:
    """Tests for CharacterRegistry.get_character() method."""

    def test_get_character_existing(self, mock_agent_type, sample_profile):
        """Returns character when it exists."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        created = registry.create_character(
            character_id="char_1",
            type_name="mock",
            profile=sample_profile,
            properties={},
            instructions="",
        )

        result = registry.get_character("char_1")

        assert result is created

    def test_get_character_missing_raises_keyerror(self, mock_agent_type):
        """Raises KeyError for missing character."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        with pytest.raises(KeyError):
            registry.get_character("nonexistent")


class TestCharacterRegistryHasCharacter:
    """Tests for CharacterRegistry.has_character() method."""

    def test_has_character_true(self, mock_agent_type, sample_profile):
        """Returns True when character exists."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        registry.create_character(
            character_id="char_1",
            type_name="mock",
            profile=sample_profile,
            properties={},
            instructions="",
        )

        assert registry.has_character("char_1") is True

    def test_has_character_false(self, mock_agent_type):
        """Returns False when character doesn't exist."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        assert registry.has_character("nonexistent") is False


class TestCharacterRegistryListCharacters:
    """Tests for CharacterRegistry.list_characters() method."""

    def test_list_characters_empty(self, mock_agent_type):
        """Empty registry returns empty list."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        assert registry.list_characters() == []

    def test_list_characters_multiple(self, mock_agent_type, sample_profile):
        """Returns list of all character IDs."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        registry.create_character("char_1", "mock", sample_profile, {}, "")
        registry.create_character("char_2", "mock", sample_profile, {}, "")
        registry.create_character("char_3", "mock", sample_profile, {}, "")

        result = registry.list_characters()

        assert len(result) == 3
        assert "char_1" in result
        assert "char_2" in result
        assert "char_3" in result


class TestCharacterRegistryGetAllMemories:
    """Tests for CharacterRegistry.get_all_memories() method."""

    def test_get_all_memories_empty(self, mock_agent_type):
        """Empty registry returns empty dict."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        result = registry.get_all_memories()

        assert result == {}

    def test_get_all_memories_with_characters(self, mock_agent_type, sample_profile):
        """Returns memories for all characters."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        registry.create_character("char_1", "mock", sample_profile, {}, "")
        registry.create_character("char_2", "mock", sample_profile, {}, "")

        result = registry.get_all_memories()

        assert "char_1" in result
        assert "char_2" in result
        assert isinstance(result["char_1"], CharacterMemory)
        assert isinstance(result["char_2"], CharacterMemory)


class TestCharacterRegistryRestoreMemories:
    """Tests for CharacterRegistry.restore_memories() method."""

    def test_restore_memories_existing_character(self, mock_agent_type, sample_profile):
        """Memory is restored to existing character."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        registry.create_character("char_1", "mock", sample_profile, {}, "")

        new_memory = CharacterMemory()
        new_memory.add_knowledge(fact="Restored fact")

        registry.restore_memories({"char_1": new_memory})

        char = registry.get_character("char_1")
        assert char.memory is new_memory

    @patch("agents.character.registry.log")
    def test_restore_memories_missing_character_logs_warning(
        self, mock_log, mock_agent_type
    ):
        """Warning is logged for missing character."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        memory = CharacterMemory()

        registry.restore_memories({"nonexistent": memory})

        mock_log.warning.assert_called_with(
            "memory_restore_skipped",
            character_id="nonexistent",
            reason="character not found",
        )


class TestCharacterRegistryListAgentTypes:
    """Tests for CharacterRegistry.list_agent_types() method."""

    def test_list_agent_types_empty(self):
        """Empty registry returns empty list."""
        registry = CharacterRegistry()

        assert registry.list_agent_types() == []

    def test_list_agent_types_sorted(self, mock_agent_type):
        """Returns sorted list of agent type names."""
        type_z = MagicMock()
        type_z.name = "z_type"
        type_a = MagicMock()
        type_a.name = "a_type"

        registry = CharacterRegistry(
            agent_types={"z_type": type_z, "a_type": type_a, "mock": mock_agent_type}
        )

        result = registry.list_agent_types()

        assert result == ["a_type", "mock", "z_type"]


class TestCharacterRegistryGetAgentType:
    """Tests for CharacterRegistry.get_agent_type() method."""

    def test_get_agent_type_existing(self, mock_agent_type):
        """Returns agent type when it exists."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        result = registry.get_agent_type("mock")

        assert result is mock_agent_type

    def test_get_agent_type_missing_raises_keyerror(self, mock_agent_type):
        """Raises KeyError for missing agent type."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        with pytest.raises(KeyError):
            registry.get_agent_type("nonexistent")


class TestCharacterRegistryContains:
    """Tests for CharacterRegistry.__contains__() method."""

    def test_contains_existing_character(self, mock_agent_type, sample_profile):
        """Returns True for existing character."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        registry.create_character("char_1", "mock", sample_profile, {}, "")

        assert "char_1" in registry

    def test_contains_missing_character(self, mock_agent_type):
        """Returns False for missing character."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        assert "nonexistent" not in registry


class TestCharacterRegistryLen:
    """Tests for CharacterRegistry.__len__() method."""

    def test_len_empty(self, mock_agent_type):
        """Empty registry has length 0."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})

        assert len(registry) == 0

    def test_len_with_characters(self, mock_agent_type, sample_profile):
        """Registry length equals number of characters."""
        registry = CharacterRegistry(agent_types={"mock": mock_agent_type})
        registry.create_character("char_1", "mock", sample_profile, {}, "")
        registry.create_character("char_2", "mock", sample_profile, {}, "")

        assert len(registry) == 2
