"""State schema for story generation graph."""

import operator
from typing import Annotated

from typing_extensions import TypedDict

from agents.character.registry import CharacterRegistry
from langgraph.channels import UntrackedValue
from models import CharacterMemory, NarratedStory, StoryArchitecture, StoryInput
from tools.registry import ToolRegistry


class StoryGenerationState(TypedDict):
    """State for the story generation graph."""

    story_input: StoryInput
    run_id: str
    tool_registry: Annotated[ToolRegistry | None, UntrackedValue]
    character_registry: Annotated[CharacterRegistry | None, UntrackedValue]
    architecture: StoryArchitecture | None
    narrated_story: NarratedStory | None
    edited_narrations: Annotated[list[str], operator.add]  # Reducer for append
    edit_history: Annotated[list[dict], operator.add]  # [{beat_reference, delta}, ...]
    current_narration_index: int
    output_dir: str
    architecture_saved: bool
    narrative_saved: bool
    character_states: dict[str, CharacterMemory]  # character_id -> memory
