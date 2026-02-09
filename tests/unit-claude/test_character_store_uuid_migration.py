"""Unit tests for CharacterStore UUID migration in load() method."""

from __future__ import annotations

import uuid

import yaml

from character_store.store import CharacterStore


class TestCharacterStoreUUIDMigration:
    """Tests for UUID migration logic in CharacterStore.load()."""

    def test_given_yaml_file_without_uuid_when_load_called_then_uuid_auto_assigned(
        self, tmp_path
    ):
        """Given a YAML file without a uuid field, when load() is called, then a UUID is auto-generated and assigned to the returned CharacterProfile."""
        # Create a legacy YAML file without UUID
        legacy_yaml = {
            "name": "Legacy Character",
            "description": "Character without UUID",
            "role": "protagonist",
            "motivations": "Survive the migration",
            "relationships": "None",
            "backstory": "Created before UUIDs",
        }
        yaml_path = tmp_path / "legacy-character.yaml"
        yaml_path.write_text(yaml.dump(legacy_yaml, default_flow_style=False))

        store = CharacterStore(library_dir=tmp_path)
        loaded = store.load("Legacy Character")

        assert hasattr(loaded, "uuid")
        assert loaded.uuid is not None
        # Verify it's a valid UUID
        parsed_uuid = uuid.UUID(loaded.uuid)
        assert parsed_uuid.version == 4

    def test_given_yaml_file_without_uuid_when_load_called_then_uuid_persisted_to_file(
        self, tmp_path
    ):
        """Given a YAML file without a uuid field, when load() is called, then the file is immediately rewritten with the UUID included."""
        # Create a legacy YAML file without UUID
        legacy_yaml = {
            "name": "Legacy Character",
            "description": "Character without UUID",
            "role": "protagonist",
            "motivations": "Survive the migration",
            "relationships": "None",
            "backstory": "Created before UUIDs",
        }
        yaml_path = tmp_path / "legacy-character.yaml"
        yaml_path.write_text(yaml.dump(legacy_yaml, default_flow_style=False))

        store = CharacterStore(library_dir=tmp_path)
        loaded = store.load("Legacy Character")

        # Read the file back and verify UUID is now present
        updated_yaml = yaml.safe_load(yaml_path.read_text())
        assert "uuid" in updated_yaml
        assert updated_yaml["uuid"] == loaded.uuid

    def test_given_yaml_file_with_uuid_when_load_called_then_uuid_preserved(
        self, tmp_path
    ):
        """Given a YAML file that already contains a uuid field, when load() is called, then the existing UUID is preserved in the returned CharacterProfile."""
        existing_uuid = str(uuid.uuid4())
        yaml_with_uuid = {
            "uuid": existing_uuid,
            "name": "Modern Character",
            "description": "Character with UUID",
            "role": "antagonist",
            "motivations": "Keep my UUID",
            "relationships": "Strong bonds",
            "backstory": "Born with UUID",
        }
        yaml_path = tmp_path / "modern-character.yaml"
        yaml_path.write_text(yaml.dump(yaml_with_uuid, default_flow_style=False))

        store = CharacterStore(library_dir=tmp_path)
        loaded = store.load("Modern Character")

        assert loaded.uuid == existing_uuid

    def test_given_yaml_file_with_uuid_when_load_called_then_file_not_rewritten(
        self, tmp_path
    ):
        """Given a YAML file with a uuid field, when load() is called, then the file is not modified (no rewrite occurs)."""
        existing_uuid = str(uuid.uuid4())
        yaml_with_uuid = {
            "uuid": existing_uuid,
            "name": "Modern Character",
            "description": "Character with UUID",
            "role": "antagonist",
            "motivations": "Keep my UUID",
            "relationships": "Strong bonds",
            "backstory": "Born with UUID",
        }
        yaml_path = tmp_path / "modern-character.yaml"
        original_content = yaml.dump(yaml_with_uuid, default_flow_style=False)
        yaml_path.write_text(original_content)

        # Record modification time before load
        mtime_before = yaml_path.stat().st_mtime

        store = CharacterStore(library_dir=tmp_path)
        store.load("Modern Character")

        # Check modification time hasn't changed
        mtime_after = yaml_path.stat().st_mtime
        assert mtime_before == mtime_after

    def test_given_yaml_file_without_uuid_when_load_called_then_uuid_added_to_index(
        self, tmp_path
    ):
        """Given a YAML file without a uuid, when load() is called after load_all(), then the newly assigned UUID is added to the UUID index."""
        # Create a legacy YAML file without UUID
        legacy_yaml = {
            "name": "Legacy Character",
            "description": "Character without UUID",
            "role": "protagonist",
            "motivations": "Survive the migration",
            "relationships": "None",
            "backstory": "Created before UUIDs",
        }
        yaml_path = tmp_path / "legacy-character.yaml"
        yaml_path.write_text(yaml.dump(legacy_yaml, default_flow_style=False))

        store = CharacterStore(library_dir=tmp_path)
        # Initialize the index
        store.load_all()

        # Now load the character (triggering migration)
        loaded = store.load("Legacy Character")

        # Verify the UUID was added to the index
        assert loaded.uuid in store._uuid_index
        assert store._uuid_index[loaded.uuid] == "legacy-character"
