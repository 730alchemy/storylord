"""Protocol definitions for storylord agents.

These protocols define the contracts that all agent implementations must follow.
External packages can implement these protocols to create custom agents.
"""

from __future__ import annotations

from typing import Protocol

from agents.character.registry import CharacterRegistry
from models import (
    ArchitectInput,
    EditedText,
    EditorInput,
    NarratedStory,
    NarratorInput,
    StoryArchitecture,
)
from tools.registry import ToolRegistry


class Architect(Protocol):
    """Protocol for story architecture generators.

    Architects are responsible for creating the structural backbone of a story,
    including plot events and story beats.
    """

    name: str

    def generate(
        self,
        input: ArchitectInput,
        tools: ToolRegistry | None = None,
    ) -> StoryArchitecture:
        """Generate a story architecture from the given input.

        Args:
            input: The architect input parameters including story idea,
                   characters, and structural requirements.
            tools: Optional registry of tools the agent can use.

        Returns:
            A complete story architecture with plot events and beats.
        """
        ...


class Narrator(Protocol):
    """Protocol for narrative generators.

    Narrators transform story architectures into prose narratives,
    bringing the structural beats to life with descriptive text and dialogue.
    """

    name: str

    def generate(
        self,
        input: NarratorInput,
        tools: ToolRegistry | None = None,
        character_registry: CharacterRegistry | None = None,
    ) -> NarratedStory:
        """Generate narrative prose from a story architecture.

        Args:
            input: The narrator input including the story architecture,
                   characters, and tone.
            tools: Optional registry of tools the agent can use.
            character_registry: Optional registry of character agent instances.

        Returns:
            A complete narrated story with prose for each beat.
        """
        ...


class Editor(Protocol):
    """Protocol for text editors.

    Editors improve and refine text, enhancing clarity, style, and quality.
    """

    name: str

    def edit(
        self,
        input: EditorInput,
        tools: ToolRegistry | None = None,
    ) -> EditedText:
        """Edit and improve the given text.

        Args:
            input: The editor input containing text to edit.
            tools: Optional registry of tools the agent can use.

        Returns:
            The edited and improved text.
        """
        ...
