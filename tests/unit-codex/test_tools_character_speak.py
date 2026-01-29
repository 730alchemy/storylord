from __future__ import annotations

import pytest

from agents.character.protocols import CharacterResponse
from tools.character_speak import CharacterSpeakTool
from tools.context import ToolExecutionContext


class DummyCharacter:
    def speak(self, speak_input):
        assert speak_input.prompt
        return CharacterResponse(content="Hello", emotional_state="happy")


class DummyRegistry:
    def __init__(self):
        self.characters = {}

    def has_character(self, character_id: str) -> bool:
        return character_id in self.characters

    def get_character(self, character_id: str):
        return self.characters[character_id]


def test_character_speak_requires_registry():
    tool = CharacterSpeakTool()

    with pytest.raises(RuntimeError, match="Character registry not available"):
        tool.execute(character_id="Test", scene_context="Scene", prompt="Say hi")


def test_character_speak_unknown_character():
    tool = CharacterSpeakTool()
    registry = DummyRegistry()
    tool.configure(ToolExecutionContext(character_registry=registry))

    with pytest.raises(KeyError, match="Unknown character"):
        tool.execute(character_id="Missing", scene_context="Scene", prompt="Say hi")


def test_character_speak_success():
    tool = CharacterSpeakTool()
    registry = DummyRegistry()
    registry.characters["Test"] = DummyCharacter()

    tool.configure(ToolExecutionContext(character_registry=registry))

    result = tool.execute(
        character_id="Test",
        scene_context="Scene",
        prompt="Say hi",
        conversation_history=["Hello"],
    )

    assert result == {
        "content": "Hello",
        "emotional_state": "happy",
        "internal_notes": "",
    }
