"""Integration tests for the CharacterStore → load_input_node round trip.

These tests exercise the shared slugify_name boundary: characters are
persisted via CharacterStore.save() and resolved via load_input_node,
verifying that the same slug is used on both sides.
"""

from __future__ import annotations

from types import SimpleNamespace

from graph.nodes import load_input_node
from character_store.store import CharacterStore
from models import CharacterAgentConfig, CharacterProfile, StoryInput


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
        from models import CharacterMemory

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


def _patch_node_deps(monkeypatch, tmp_path):
    monkeypatch.setattr("graph.nodes.ToolRegistry", DummyToolRegistry)
    monkeypatch.setattr(
        "graph.nodes.discover_character_agent_types",
        lambda: {"default": DummyAgentType(), "mbti": DummyAgentType()},
    )
    monkeypatch.setattr(
        "graph.nodes.settings",
        SimpleNamespace(character_library_dir=str(tmp_path)),
    )


class TestLibraryResolutionIntegration:
    """Round-trip tests: CharacterStore.save → load_input_node resolution."""

    def test_given_character_saved_via_store_when_referenced_in_character_library_then_load_input_resolves_it(
        self, monkeypatch, tmp_path
    ):
        """A character persisted by CharacterStore is resolvable by load_input_node."""
        store = CharacterStore(library_dir=tmp_path)
        profile = CharacterProfile(
            name="Elijah Boondog",
            description="A dentist with a passion for history",
            role="protagonist",
            motivations="Curiosity",
            relationships="Best friends with Jasper",
            backstory="Sometimes loses track of the world",
        )
        store.save(profile)
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = StoryInput(
            story_idea="Test",
            characters=[],
            num_plot_events=1,
            beats_per_event=(1, 1),
            tone="neutral",
            output_file="test",
            character_library=["Elijah Boondog"],
        )
        load_input_node({"story_input": story_input})

        assert len(story_input.characters) == 1
        resolved = story_input.characters[0]
        assert resolved.name == "Elijah Boondog"
        assert resolved.description == "A dentist with a passion for history"
        assert resolved.backstory == "Sometimes loses track of the world"

    def test_given_library_character_with_agent_config_saved_via_store_when_resolved_then_registered_in_character_registry(
        self, monkeypatch, tmp_path
    ):
        """A library character with agent_config is resolved AND registered in the character registry."""
        store = CharacterStore(library_dir=tmp_path)
        profile = CharacterProfile(
            name="Jasper Dilsack",
            description="A lawyer",
            role="protagonist",
            motivations="Winning",
            relationships="Best friends with Elijah",
            backstory="Jumped two grades",
            agent_config=CharacterAgentConfig(
                agent_type="mbti",
                agent_properties={
                    "extroversion": 90,
                    "intuition": 7,
                    "thinking": 1,
                    "judging": 99,
                },
                agent_instructions="use a lot of gen z slang",
            ),
        )
        store.save(profile)
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = StoryInput(
            story_idea="Test",
            characters=[],
            num_plot_events=1,
            beats_per_event=(1, 1),
            tone="neutral",
            output_file="test",
            character_library=["Jasper Dilsack"],
        )
        result = load_input_node({"story_input": story_input})

        # Resolved into characters list
        assert story_input.characters[0].name == "Jasper Dilsack"
        assert story_input.characters[0].agent_config is not None
        assert story_input.characters[0].agent_config.agent_type == "mbti"

        # Registered in the character registry (agent_config triggers registration)
        assert result["character_registry"].has_character("Jasper Dilsack")

    def test_given_multiple_characters_saved_via_store_when_all_referenced_then_all_resolved(
        self, monkeypatch, tmp_path
    ):
        """All characters in character_library are resolved when multiple are saved."""
        store = CharacterStore(library_dir=tmp_path)
        profiles = [
            CharacterProfile(
                name="Elijah Boondog",
                description="A dentist",
                role="protagonist",
                motivations="Curiosity",
                relationships="",
                backstory="",
            ),
            CharacterProfile(
                name="Jasper Dilsack",
                description="A lawyer",
                role="protagonist",
                motivations="Winning",
                relationships="",
                backstory="",
            ),
            CharacterProfile(
                name="Riley Thorn",
                description="A manipulator",
                role="antagonist",
                motivations="Amusement",
                relationships="",
                backstory="",
            ),
        ]
        for p in profiles:
            store.save(p)
        _patch_node_deps(monkeypatch, tmp_path)

        story_input = StoryInput(
            story_idea="Test",
            characters=[],
            num_plot_events=1,
            beats_per_event=(1, 1),
            tone="neutral",
            output_file="test",
            character_library=["Elijah Boondog", "Jasper Dilsack", "Riley Thorn"],
        )
        load_input_node({"story_input": story_input})

        names = [c.name for c in story_input.characters]
        assert names == ["Elijah Boondog", "Jasper Dilsack", "Riley Thorn"]
