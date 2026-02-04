"""Unit tests for CharacterStore.save method."""

from __future__ import annotations

from unittest.mock import patch

import yaml

from character_store.store import CharacterStore
from models import CharacterAgentConfig


class TestCharacterStoreSave:
    """Tests for CharacterStore.save()."""

    def test_given_valid_profile_when_saved_then_yaml_file_created_at_expected_path(
        self, tmp_path, sample_profile
    ):
        """Save creates a YAML file at {library_dir}/{slug}.yaml."""
        store = CharacterStore(library_dir=tmp_path)
        store.save(sample_profile)

        assert (tmp_path / "test-character.yaml").exists()

    def test_given_valid_profile_when_saved_then_returned_path_matches_written_file(
        self, tmp_path, sample_profile
    ):
        """The returned Path points to the file that was written."""
        store = CharacterStore(library_dir=tmp_path)
        result = store.save(sample_profile)

        assert result == tmp_path / "test-character.yaml"
        assert result.exists()

    def test_given_valid_profile_when_saved_then_file_content_is_valid_yaml(
        self, tmp_path, sample_profile
    ):
        """Written file parses as valid YAML with expected field values."""
        store = CharacterStore(library_dir=tmp_path)
        path = store.save(sample_profile)

        loaded = yaml.safe_load(path.read_text())
        assert loaded["name"] == "Test Character"
        assert loaded["role"] == "protagonist"
        assert loaded["description"] == "A test character for unit testing"

    def test_given_profile_with_agent_config_when_saved_then_agent_config_present_in_yaml(
        self, tmp_path, sample_profile
    ):
        """agent_config block is present in YAML when set on the profile."""
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
        path = store.save(sample_profile)

        loaded = yaml.safe_load(path.read_text())
        assert "agent_config" in loaded
        assert loaded["agent_config"]["agent_type"] == "mbti"
        assert loaded["agent_config"]["agent_properties"]["extroversion"] == 80
        assert loaded["agent_config"]["agent_instructions"] == "Speak casually"

    def test_given_profile_without_agent_config_when_saved_then_agent_config_absent_from_yaml(
        self, tmp_path, sample_profile
    ):
        """agent_config key is absent from YAML when None on the profile."""
        assert sample_profile.agent_config is None
        store = CharacterStore(library_dir=tmp_path)
        path = store.save(sample_profile)

        loaded = yaml.safe_load(path.read_text())
        assert "agent_config" not in loaded

    def test_given_existing_character_file_when_saved_again_then_file_is_overwritten(
        self, tmp_path, sample_profile
    ):
        """Saving a character whose file already exists overwrites with new content."""
        store = CharacterStore(library_dir=tmp_path)
        store.save(sample_profile)

        sample_profile.description = "Updated description"
        path = store.save(sample_profile)

        loaded = yaml.safe_load(path.read_text())
        assert loaded["description"] == "Updated description"

    def test_given_library_dir_does_not_exist_when_saved_then_directory_is_created(
        self, tmp_path, sample_profile
    ):
        """save() creates the library directory if it doesn't exist."""
        nested = tmp_path / "a" / "b" / "characters"
        store = CharacterStore(library_dir=nested)
        store.save(sample_profile)

        assert nested.exists()
        assert (nested / "test-character.yaml").exists()

    def test_given_existing_character_file_when_saved_again_then_backup_created_with_old_extension_and_warning_logged(
        self, tmp_path, sample_profile
    ):
        """Overwriting an existing character creates a .old backup and logs a warning."""
        store = CharacterStore(library_dir=tmp_path)
        path = store.save(sample_profile)
        original_content = path.read_text()

        sample_profile.description = "Updated description"
        with patch("character_store.store.log") as mock_log:
            store.save(sample_profile)
            mock_log.warning.assert_called_once()

        backup = tmp_path / "test-character.yaml.old"
        assert backup.exists()
        assert backup.read_text() == original_content
