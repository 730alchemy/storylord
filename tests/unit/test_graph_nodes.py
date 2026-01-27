from __future__ import annotations

from datetime import datetime

import pytest

from graph.delta import compute_text_delta
from graph.nodes import (
    editor_node,
    load_input_node,
    save_architecture_node,
    save_narrative_node,
    should_continue_editing,
)
from models import (
    BeatNarration,
    CharacterAgentConfig,
    CharacterMemory,
    CharacterProfile,
    NarratedStory,
    StoryArchitecture,
    StoryBeat,
    StoryInput,
    PlotEvent,
)


class DummyToolRegistry:
    def __init__(self, tool_names):
        self.tool_names = tool_names
        self.configured = False
        self.context = None

    def configure(self, context):
        self.configured = True
        self.context = context


class DummyCharacter:
    def __init__(self):
        self.memory = CharacterMemory()


class DummyAgentType:
    def create_instance(
        self,
        character_id,
        character_profile,
        type_properties,
        instructions,
        initial_memory=None,
    ):
        return DummyCharacter()


class DummyEditor:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text

    def edit(self, _input):
        from models import EditedText

        return EditedText(text=self.output_text)


class FixedDatetime:
    @classmethod
    def now(cls):
        return datetime(2024, 1, 2, 3, 4, 5)


def _make_story_input() -> StoryInput:
    profile = CharacterProfile(
        name="Test",
        description="Desc",
        role="protagonist",
        motivations="Motivation",
        relationships="None",
        backstory="Backstory",
        agent_config=CharacterAgentConfig(agent_type="default"),
    )
    return StoryInput(
        story_idea="Idea",
        characters=[profile],
        num_plot_events=1,
        beats_per_event=(1, 1),
        tone="tone",
        output_file="output",
    )


def test_load_input_node_adds_character_speak(monkeypatch: pytest.MonkeyPatch) -> None:
    story_input = _make_story_input()

    monkeypatch.setattr("graph.nodes.ToolRegistry", DummyToolRegistry)
    monkeypatch.setattr(
        "graph.nodes.discover_character_agent_types",
        lambda: {"default": DummyAgentType()},
    )

    result = load_input_node({"story_input": story_input})

    assert "character_speak" in result["tool_registry"].tool_names
    assert result["character_registry"].has_character("Test")
    assert result["tool_registry"].configured is True
    assert result["tool_registry"].context.run_id == result["run_id"]


def test_editor_node_increments_and_records(monkeypatch: pytest.MonkeyPatch) -> None:
    narration = BeatNarration(
        narrative_text="Original text",
        beat_reference="Event 1, Beat 1",
    )
    state = {
        "narrated_story": NarratedStory(narrations=[narration]),
        "current_narration_index": 0,
    }

    monkeypatch.setattr("graph.nodes.get_editor", lambda _name: DummyEditor("Edited"))

    result = editor_node(state)

    assert result["current_narration_index"] == 1
    assert result["edited_narrations"] == ["Edited"]
    assert result["edit_history"][0]["beat_reference"] == "Event 1, Beat 1"
    assert result["edit_history"][0]["delta"] == compute_text_delta(
        "Original text", "Edited"
    )


def test_save_architecture_node_writes_file(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr("graph.nodes.datetime", FixedDatetime)

    architecture = StoryArchitecture(
        plot_events=[
            PlotEvent(
                title="Event",
                summary="Summary",
                beats=[
                    StoryBeat(
                        description="Beat",
                        beat_type="action",
                        characters_involved=[],
                    )
                ],
            )
        ]
    )

    state = {
        "architecture_saved": False,
        "story_input": _make_story_input(),
        "architecture": architecture,
        "output_dir": str(tmp_path),
    }

    result = save_architecture_node(state)
    assert result == {"architecture_saved": True}

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].name.startswith("output_architecture_20240102_030405")
    assert "plot_events" in files[0].read_text()


def test_save_architecture_node_idempotent(tmp_path):
    state = {
        "architecture_saved": True,
        "story_input": _make_story_input(),
        "architecture": None,
        "output_dir": str(tmp_path),
    }

    assert save_architecture_node(state) == {}
    assert list(tmp_path.iterdir()) == []


def test_save_narrative_node_writes_file(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr("graph.nodes.datetime", FixedDatetime)

    state = {
        "narrative_saved": False,
        "story_input": _make_story_input(),
        "edited_narrations": ["First", "Second"],
        "output_dir": str(tmp_path),
    }

    result = save_narrative_node(state)
    assert result == {"narrative_saved": True}

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].name.startswith("output_narrative_20240102_030405")
    content = files[0].read_text()
    assert content == "First\n\nSecond"


def test_save_narrative_node_idempotent(tmp_path):
    state = {
        "narrative_saved": True,
        "story_input": _make_story_input(),
        "edited_narrations": [],
        "output_dir": str(tmp_path),
    }

    assert save_narrative_node(state) == {}
    assert list(tmp_path.iterdir()) == []


def test_should_continue_editing():
    story = NarratedStory(
        narrations=[BeatNarration(narrative_text="a", beat_reference="Event 1, Beat 1")]
    )

    assert (
        should_continue_editing({"narrated_story": story, "current_narration_index": 0})
        == "editor"
    )
    assert (
        should_continue_editing({"narrated_story": story, "current_narration_index": 1})
        == "save_narrative"
    )
