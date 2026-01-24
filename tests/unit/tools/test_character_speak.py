"""Unit tests for CharacterSpeakTool class."""

from unittest.mock import MagicMock

import pytest

from tools.character_speak import CharacterSpeakTool
from tools.context import ToolExecutionContext


@pytest.fixture
def tool():
    """Create a fresh CharacterSpeakTool instance."""
    return CharacterSpeakTool()


@pytest.fixture
def mock_registry():
    """Create a mock character registry."""
    registry = MagicMock()
    registry.has_character = MagicMock(return_value=True)
    mock_character = MagicMock()
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "dialogue": "Hello there!",
        "internal_thought": "Greeting them warmly",
    }
    mock_character.speak = MagicMock(return_value=mock_response)
    registry.get_character = MagicMock(return_value=mock_character)
    return registry


@pytest.fixture
def configured_tool(tool, mock_registry):
    """Create a CharacterSpeakTool configured with a mock registry."""
    context = ToolExecutionContext(character_registry=mock_registry)
    tool.configure(context)
    return tool


class TestCharacterSpeakToolGetSchema:
    """Tests for CharacterSpeakTool.get_schema() method."""

    def test_get_schema_returns_valid_json_schema(self, tool):
        """Schema is a valid JSON schema object."""
        schema = tool.get_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_get_schema_has_required_fields(self, tool):
        """Schema requires character_id, scene_context, and prompt."""
        schema = tool.get_schema()

        assert "character_id" in schema["required"]
        assert "scene_context" in schema["required"]
        assert "prompt" in schema["required"]

    def test_get_schema_conversation_history_is_optional(self, tool):
        """conversation_history is not in required fields."""
        schema = tool.get_schema()

        assert "conversation_history" not in schema["required"]
        assert "conversation_history" in schema["properties"]

    def test_get_schema_property_types(self, tool):
        """Schema properties have correct types."""
        schema = tool.get_schema()
        props = schema["properties"]

        assert props["character_id"]["type"] == "string"
        assert props["scene_context"]["type"] == "string"
        assert props["prompt"]["type"] == "string"
        assert props["conversation_history"]["type"] == "array"
        assert props["conversation_history"]["items"]["type"] == "string"

    def test_get_schema_has_descriptions(self, tool):
        """All properties have descriptions."""
        schema = tool.get_schema()
        props = schema["properties"]

        for prop_name, prop_def in props.items():
            assert "description" in prop_def, (
                f"Property {prop_name} missing description"
            )


class TestCharacterSpeakToolConfigure:
    """Tests for CharacterSpeakTool.configure() method."""

    def test_configure_stores_context(self, tool, mock_registry):
        """Configure stores the provided context."""
        context = ToolExecutionContext(
            character_registry=mock_registry,
            run_id="test-123",
        )

        tool.configure(context)

        assert tool._context is context


class TestCharacterSpeakToolExecute:
    """Tests for CharacterSpeakTool.execute() method."""

    def test_execute_no_context_raises_runtimeerror(self, tool):
        """Raises RuntimeError when no context configured."""
        with pytest.raises(RuntimeError) as exc_info:
            tool.execute(
                character_id="char_1",
                scene_context="A scene",
                prompt="Say hello",
            )

        assert "Character registry not available" in str(exc_info.value)

    def test_execute_no_registry_raises_runtimeerror(self, tool):
        """Raises RuntimeError when context has no registry."""
        context = ToolExecutionContext(character_registry=None)
        tool.configure(context)

        with pytest.raises(RuntimeError) as exc_info:
            tool.execute(
                character_id="char_1",
                scene_context="A scene",
                prompt="Say hello",
            )

        assert "Character registry not available" in str(exc_info.value)

    def test_execute_unknown_character_raises_keyerror(self, tool, mock_registry):
        """Raises KeyError when character not in registry."""
        mock_registry.has_character.return_value = False
        context = ToolExecutionContext(character_registry=mock_registry)
        tool.configure(context)

        with pytest.raises(KeyError) as exc_info:
            tool.execute(
                character_id="unknown_char",
                scene_context="A scene",
                prompt="Say hello",
            )

        assert "Unknown character 'unknown_char'" in str(exc_info.value)

    def test_execute_success(self, configured_tool, mock_registry):
        """Successful execution returns response dict."""
        result = configured_tool.execute(
            character_id="char_1",
            scene_context="A cafe scene",
            prompt="Greet the barista",
        )

        assert result == {
            "dialogue": "Hello there!",
            "internal_thought": "Greeting them warmly",
        }

    def test_execute_passes_conversation_history(self, configured_tool, mock_registry):
        """Conversation history is passed to character speak."""
        history = ["Hello!", "Hi there!"]

        configured_tool.execute(
            character_id="char_1",
            scene_context="A scene",
            prompt="Continue the conversation",
            conversation_history=history,
        )

        # Verify speak was called with SpeakInput containing history
        mock_char = mock_registry.get_character.return_value
        call_args = mock_char.speak.call_args[0][0]
        assert call_args.conversation_history == history

    def test_execute_default_empty_history(self, configured_tool, mock_registry):
        """None conversation_history becomes empty list."""
        configured_tool.execute(
            character_id="char_1",
            scene_context="A scene",
            prompt="Say something",
            conversation_history=None,
        )

        mock_char = mock_registry.get_character.return_value
        call_args = mock_char.speak.call_args[0][0]
        assert call_args.conversation_history == []

    def test_execute_passes_scene_context(self, configured_tool, mock_registry):
        """Scene context is passed to character speak."""
        configured_tool.execute(
            character_id="char_1",
            scene_context="In a dark alley",
            prompt="Whisper a warning",
        )

        mock_char = mock_registry.get_character.return_value
        call_args = mock_char.speak.call_args[0][0]
        assert call_args.scene_context == "In a dark alley"

    def test_execute_passes_prompt(self, configured_tool, mock_registry):
        """Prompt is passed to character speak."""
        configured_tool.execute(
            character_id="char_1",
            scene_context="A scene",
            prompt="Express frustration",
        )

        mock_char = mock_registry.get_character.return_value
        call_args = mock_char.speak.call_args[0][0]
        assert call_args.prompt == "Express frustration"

    def test_execute_ignores_extra_kwargs(self, configured_tool, mock_registry):
        """Extra keyword arguments are ignored."""
        # Should not raise
        result = configured_tool.execute(
            character_id="char_1",
            scene_context="A scene",
            prompt="Say hi",
            extra_param="ignored",
            another_param=123,
        )

        assert "dialogue" in result
