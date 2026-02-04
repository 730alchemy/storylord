"""Unit tests for CharacterStore.load method."""

from __future__ import annotations

import pytest
import yaml

from character_store.store import CharacterStore
from models import CharacterAgentConfig


class TestCharacterStoreLoad:
    """Tests for CharacterStore.load()."""

    def test_given_saved_character_when_loaded_by_name_then_returns_matching_CharacterProfile(
        self, tmp_path, sample_profile
    ):
        """Loading a saved character by name round-trips to an equivalent profile."""
        store = CharacterStore(library_dir=tmp_path)
        store.save(sample_profile)

        loaded = store.load(sample_profile.name)

        assert loaded.name == sample_profile.name
        assert loaded.description == sample_profile.description
        assert loaded.role == sample_profile.role
        assert loaded.motivations == sample_profile.motivations
        assert loaded.relationships == sample_profile.relationships
        assert loaded.backstory == sample_profile.backstory

    def test_given_saved_character_with_agent_config_when_loaded_then_agent_config_is_populated(
        self, tmp_path, sample_profile
    ):
        """agent_config round-trips correctly through save and load."""
        sample_profile.agent_config = CharacterAgentConfig(
            agent_type="mbti",
            agent_properties={
                "extroversion": 80,
                "intuition": 60,
                "thinking": 40,
                "judging": 70,
            },
            agent_instructions="Speak casually",
        )
        store = CharacterStore(library_dir=tmp_path)
        store.save(sample_profile)

        loaded = store.load(sample_profile.name)

        assert loaded.agent_config is not None
        assert loaded.agent_config.agent_type == "mbti"
        assert loaded.agent_config.agent_properties["extroversion"] == 80
        assert loaded.agent_config.agent_instructions == "Speak casually"

    def test_given_saved_character_without_agent_config_when_loaded_then_agent_config_is_None(
        self, tmp_path, sample_profile
    ):
        """Profile with no agent_config loads back with agent_config as None."""
        assert sample_profile.agent_config is None
        store = CharacterStore(library_dir=tmp_path)
        store.save(sample_profile)

        loaded = store.load(sample_profile.name)

        assert loaded.agent_config is None

    def test_given_nonexistent_character_name_when_loaded_then_raises_FileNotFoundError(
        self, tmp_path
    ):
        """Loading a name with no file on disk raises FileNotFoundError."""
        store = CharacterStore(library_dir=tmp_path)

        with pytest.raises(FileNotFoundError):
            store.load("Nobody Here")

    def test_given_corrupt_yaml_file_when_loaded_then_raises_ValidationError(
        self, tmp_path
    ):
        """A YAML file that doesn't match CharacterProfile raises a Pydantic ValidationError."""
        from pydantic import ValidationError

        corrupt = {
            "name": "Broken",
            "role": 12345,
        }  # missing required fields, wrong types
        (tmp_path / "broken.yaml").write_text(
            yaml.dump(corrupt, default_flow_style=False)
        )
        store = CharacterStore(library_dir=tmp_path)

        with pytest.raises(ValidationError):
            store.load("Broken")
