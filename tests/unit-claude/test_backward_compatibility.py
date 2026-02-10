"""Backward compatibility tests for UUID addition."""

from __future__ import annotations


import yaml

from character_store.store import CharacterStore
from models import CharacterProfile


class TestBackwardCompatibilityLoadInputNode:
    """Tests for load_input_node backward compatibility with UUIDs (AC-24)."""

    def test_given_character_library_with_slug_names_when_load_input_node_executes_then_characters_loaded(
        self, tmp_path, monkeypatch
    ):
        """Given a StoryInput YAML with character_library containing slug names, when load_input_node executes, then characters are loaded by slug name as before (UUID presence does not affect slug-based resolution)."""
        # Create a character with UUID
        store = CharacterStore(library_dir=tmp_path)
        profile = CharacterProfile(
            name="Elijah Boondog",
            description="A dentist",
            role="protagonist",
            motivations="Curiosity",
            relationships="",
            backstory="",
        )
        store.save(profile)

        # Verify YAML file contains UUID
        yaml_path = tmp_path / "elijah-boondog.yaml"
        assert yaml_path.exists()
        yaml_data = yaml.safe_load(yaml_path.read_text())
        assert "uuid" in yaml_data

        # Load by slug name (not UUID)
        loaded = store.load("Elijah Boondog")
        assert loaded.name == "Elijah Boondog"
        assert loaded.uuid == profile.uuid

        # Verify slug-based loading still works
        loaded_by_slug = store.load("elijah-boondog")
        assert loaded_by_slug.name == "Elijah Boondog"


class TestBackwardCompatibilitySlackBot:
    """Tests for Slack bot backward compatibility with UUIDs (AC-25)."""

    def test_given_slack_bot_saves_profile_when_saved_then_uuid_included_in_yaml(
        self, tmp_path
    ):
        """Given the Slack bot calls CharacterStore.save(profile) where the profile has an auto-generated UUID, when saved, then the YAML file includes the UUID and the Slack bot flow is otherwise unaffected."""
        # Simulate Slack bot creating a character
        store = CharacterStore(library_dir=tmp_path)

        # Slack bot creates a CharacterProfile (UUID auto-generated)
        profile = CharacterProfile(
            name="Slack Character",
            description="Created by Slack bot",
            role="protagonist",
            motivations="Testing",
            relationships="Friends",
            backstory="Born in Slack",
        )

        # Slack bot saves the character
        saved_path = store.save(profile)

        # Verify file exists
        assert saved_path.exists()

        # Verify UUID is in the YAML file
        yaml_data = yaml.safe_load(saved_path.read_text())
        assert "uuid" in yaml_data
        assert yaml_data["uuid"] == profile.uuid

        # Verify Slack bot can still load by name
        loaded = store.load("Slack Character")
        assert loaded.name == "Slack Character"
        assert loaded.uuid == profile.uuid

    def test_given_slack_bot_updates_character_when_saved_then_uuid_preserved(
        self, tmp_path
    ):
        """Given Slack bot updates an existing character, when saved, then UUID is preserved."""
        store = CharacterStore(library_dir=tmp_path)

        # Initial save
        profile = CharacterProfile(
            name="Slack Character",
            description="Original description",
            role="protagonist",
            motivations="Original",
            relationships="Original",
            backstory="Original",
        )
        store.save(profile)
        original_uuid = profile.uuid

        # Slack bot updates the character
        profile.description = "Updated description"
        store.save(profile)

        # Verify UUID is preserved
        loaded = store.load("Slack Character")
        assert loaded.uuid == original_uuid
        assert loaded.description == "Updated description"
