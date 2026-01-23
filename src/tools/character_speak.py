"""Tool wrapper for character agent dialogue."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass
from tools.context import ToolExecutionContext


class CharacterSpeakTool:
    """Call a character agent to generate dialogue."""

    name = "character_speak"
    description = "Generate in-character dialogue using the specified character agent."

    def __init__(self) -> None:
        self._context: ToolExecutionContext | None = None

    def configure(self, context: ToolExecutionContext) -> None:
        self._context = context

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "character_id": {
                    "type": "string",
                    "description": "Exact character ID/name to speak.",
                },
                "scene_context": {
                    "type": "string",
                    "description": "Brief scene context for this line.",
                },
                "prompt": {
                    "type": "string",
                    "description": "Instruction for what the character should say.",
                },
                "conversation_history": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Prior dialogue lines, if any.",
                },
            },
            "required": ["character_id", "scene_context", "prompt"],
        }

    def execute(
        self,
        character_id: str,
        scene_context: str,
        prompt: str,
        conversation_history: list[str] | None = None,
        **_: Any,
    ) -> dict:
        if not self._context or not self._context.character_registry:
            raise RuntimeError("Character registry not available for tool execution.")

        registry = self._context.character_registry
        if not registry.has_character(character_id):
            raise KeyError(f"Unknown character '{character_id}'.")

        from agents.character.protocols import SpeakInput

        speak_input = SpeakInput(
            scene_context=scene_context,
            conversation_history=conversation_history or [],
            prompt=prompt,
        )
        response = registry.get_character(character_id).speak(speak_input)
        return response.model_dump()
