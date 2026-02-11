"""Unit tests for character_library resolution in load_input_node."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from graph.nodes import load_input_node
from models import CharacterProfile, StoryInput


class DummyToolRegistry:
    def __init__(self, tool_names):
        self.tool_names = tool_names
        self.configured = False
        self.context = None

    def configure(self, context):
        self.configured = True
        self.context = context


class DummyAgentType:
    def create_instance(
        self,
        character_id,
        character_profile,
        type_properties,
        instructions,
        initial_memory=None,
    ):
        from models import CharacterMemory

        class _Agent:
            def __init__(self):
                self.memory = CharacterMemory()

        return _Agent()


def _write_character_yaml(directory: Path, profile: CharacterProfile) -> None:
    """Write a CharacterProfile as a YAML file using the same conventions as CharacterStore."""
    from character_store.slugify import slugify_name

    data = profile.model_dump(mode="json", exclude_none=True)
    (directory / f"{slugify_name(profile.name)}.yaml").write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False)
    )


def _base_story_input(
    characters: list[CharacterProfile] | None = None,
    character_library: list[str] | None = None,
) -> StoryInput:
    """Build a minimal StoryInput for testing."""
    return StoryInput(
        story_idea="Test",
        characters=characters or [],
        num_plot_events=1,
        beats_per_event=(1, 1),
        tone="neutral",
        output_file="test",
        character_library=character_library or [],
    )


def _patch_node_deps(monkeypatch, tmp_path):
    """Monkeypatch the three dependencies load_input_node uses."""
    monkeypatch.setattr("graph.nodes.ToolRegistry", DummyToolRegistry)
    monkeypatch.setattr(
        "graph.nodes.discover_character_agent_types",
        lambda: {"default": DummyAgentType()},
    )
    monkeypatch.setattr(
        "graph.nodes.get_settings",
        lambda: SimpleNamespace(character_library_dir=str(tmp_path)),
    )


class TestCharacterLibraryResolution:
    """Tests for character_library resolution in load_input_node."""

    def test_given_character_library_with_valid_names_when_load_input_runs_then_library_characters_appended(
        self, monkeypatch, tmp_path
    ):
        """Characters referenced in character_library are loaded and appended."""
        profile = CharacterProfile(
            name="Elijah Boondog",
            description="A dentist",
            role="protagonist",
            motivations="Curiosity",
            relationships="",
            backstory="",
        )
        _write_character_yaml(tmp_path, profile)
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = _base_story_input(character_library=["Elijah Boondog"])
        load_input_node({"story_input": story_input})

        assert len(story_input.characters) == 1
        assert story_input.characters[0].name == "Elijah Boondog"

    def test_given_character_library_referencing_missing_character_when_load_input_runs_then_raises_FileNotFoundError(
        self, monkeypatch, tmp_path
    ):
        """A character_library entry with no matching file raises FileNotFoundError."""
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = _base_story_input(character_library=["Nobody Here"])

        with pytest.raises(FileNotFoundError, match="Nobody Here"):
            load_input_node({"story_input": story_input})

    def test_given_empty_character_library_when_load_input_runs_then_only_inline_characters_present(
        self, monkeypatch, tmp_path
    ):
        """An empty character_library leaves only inline characters untouched."""
        inline = CharacterProfile(
            name="Inline Char",
            description="Defined inline",
            role="supporting",
            motivations="Testing",
            relationships="",
            backstory="",
        )
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = _base_story_input(characters=[inline])
        load_input_node({"story_input": story_input})

        assert len(story_input.characters) == 1
        assert story_input.characters[0].name == "Inline Char"

    def test_given_character_library_alongside_inline_characters_when_load_input_runs_then_both_present(
        self, monkeypatch, tmp_path
    ):
        """Library characters and inline characters coexist in the final list."""
        library_profile = CharacterProfile(
            name="Library Char",
            description="From library",
            role="antagonist",
            motivations="Villainy",
            relationships="",
            backstory="",
        )
        _write_character_yaml(tmp_path, library_profile)

        inline_profile = CharacterProfile(
            name="Inline Char",
            description="Defined inline",
            role="protagonist",
            motivations="Testing",
            relationships="",
            backstory="",
        )
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = _base_story_input(
            characters=[inline_profile],
            character_library=["Library Char"],
        )
        load_input_node({"story_input": story_input})

        names = [c.name for c in story_input.characters]
        assert "Inline Char" in names
        assert "Library Char" in names
        assert len(story_input.characters) == 2
