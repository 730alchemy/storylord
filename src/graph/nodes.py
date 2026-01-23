"""Node functions for story generation graph."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

import structlog

from agents.character.registry import CharacterRegistry
from agents.discovery import (
    discover_character_agent_types,
    get_architect,
    get_editor,
    get_narrator,
)
from graph.delta import compute_text_delta
from graph.state import StoryGenerationState
from models import ArchitectInput, EditorInput, NarratorInput
from tools.context import ToolExecutionContext
from tools.registry import ToolRegistry

log = structlog.get_logger(__name__)


def load_input_node(state: StoryGenerationState) -> dict:
    """Initialize tool_registry, character_registry, and tracking flags."""
    story_input = state["story_input"]
    run_id = uuid.uuid4().hex
    tool_names = list(story_input.tools or [])
    if any(char.agent_config for char in story_input.characters):
        if "character_speak" not in tool_names:
            tool_names.append("character_speak")
            log.info(
                "tool_added",
                tool="character_speak",
                reason="character_agents_present",
            )
    tool_registry = ToolRegistry(tool_names) if tool_names else None

    # Create character registry and populate with characters that have agent_config
    agent_types = discover_character_agent_types()
    character_registry = CharacterRegistry(agent_types=agent_types)

    for char in story_input.characters:
        if char.agent_config:
            character_registry.create_character(
                character_id=char.name,
                type_name=char.agent_config.agent_type,
                profile=char,
                properties=char.agent_config.agent_properties,
                instructions=char.agent_config.agent_instructions,
            )

    if tool_registry:
        tool_registry.configure(
            ToolExecutionContext(
                character_registry=character_registry,
                run_id=run_id,
            )
        )

    return {
        "run_id": run_id,
        "tool_registry": tool_registry,
        "character_registry": character_registry,
    }


def architect_node(state: StoryGenerationState) -> dict:
    """Run the architect agent to generate story architecture."""
    story_input = state["story_input"]
    tool_registry = state["tool_registry"]

    architect = get_architect(story_input.architect)
    log.info("running_architect", architect=story_input.architect)

    architect_input = ArchitectInput(
        story_idea=story_input.story_idea,
        characters=story_input.characters,
        num_plot_events=story_input.num_plot_events,
        beats_per_event=story_input.beats_per_event,
        tone=story_input.tone,
    )
    architecture = architect.generate(architect_input, tools=tool_registry)

    return {"architecture": architecture}


def save_architecture_node(state: StoryGenerationState) -> dict:
    """Save architecture to JSON file (idempotent)."""
    if state["architecture_saved"]:
        return {}

    story_input = state["story_input"]
    architecture = state["architecture"]
    output_dir = Path(state["output_dir"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir.mkdir(exist_ok=True)
    arch_path = output_dir / f"{story_input.output_file}_architecture_{timestamp}.json"
    arch_path.write_text(architecture.model_dump_json(indent=2))
    log.info("architecture_saved", path=str(arch_path))

    return {"architecture_saved": True}


def narrator_node(state: StoryGenerationState) -> dict:
    """Run the narrator agent to generate narrations."""
    story_input = state["story_input"]
    architecture = state["architecture"]
    tool_registry = state["tool_registry"]
    character_registry = state["character_registry"]

    narrator = get_narrator(story_input.narrator)
    log.info("running_narrator", narrator=story_input.narrator)

    narrator_input = NarratorInput(
        story_architecture=architecture,
        characters=story_input.characters,
        tone=story_input.tone,
        run_id=state.get("run_id"),
    )
    narrated_story = narrator.generate(
        narrator_input,
        tools=tool_registry,
        character_registry=character_registry,
    )

    # Persist character memories to state
    character_states = {}
    if character_registry:
        character_states = character_registry.get_all_memories()

    return {
        "narrated_story": narrated_story,
        "character_states": character_states,
    }


def editor_node(state: StoryGenerationState) -> dict:
    """Edit one narration at a time for checkpoint granularity."""
    narrated_story = state["narrated_story"]
    current_index = state["current_narration_index"]

    narration = narrated_story.narrations[current_index]

    log.info("running_editor", editor="simile-smasher")
    editor = get_editor("simile-smasher")
    editor_input = EditorInput(text=narration.narrative_text)
    edited = editor.edit(editor_input)

    # Compute and log delta
    delta = compute_text_delta(narration.narrative_text, edited.text)
    log.info("narration_edited", beat_reference=narration.beat_reference, delta=delta)

    return {
        "edited_narrations": [edited.text],  # Uses reducer to append
        "current_narration_index": current_index + 1,
        "edit_history": [{"beat_reference": narration.beat_reference, "delta": delta}],
    }


def save_narrative_node(state: StoryGenerationState) -> dict:
    """Save narrative to text file (idempotent)."""
    if state["narrative_saved"]:
        return {}

    story_input = state["story_input"]
    edited_narrations = state["edited_narrations"]
    output_dir = Path(state["output_dir"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir.mkdir(exist_ok=True)
    narrative_path = output_dir / f"{story_input.output_file}_narrative_{timestamp}.txt"
    narrative_text = "\n\n".join(edited_narrations)
    narrative_path.write_text(narrative_text)
    log.info("narrative_saved", path=str(narrative_path))

    return {"narrative_saved": True}


def should_continue_editing(
    state: StoryGenerationState,
) -> Literal["editor", "save_narrative"]:
    """Determine if there are more narrations to edit."""
    narrated_story = state["narrated_story"]
    current_index = state["current_narration_index"]

    if current_index < len(narrated_story.narrations):
        return "editor"
    return "save_narrative"
