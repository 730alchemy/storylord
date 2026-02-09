"""Unit tests for CharacterStore.save name change handling."""

from __future__ import annotations

from character_store.store import CharacterStore
from models import CharacterProfile


class TestCharacterStoreSaveRename:
    """Tests for name change handling in CharacterStore.save()."""

    def test_given_character_name_unchanged_when_saved_then_index_updated(
        self, tmp_path
    ):
        """Given a character is saved without name change, when save() completes, then the UUID index is updated with current slug."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="Test Character",
            description="A test",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Test",
        )
        store.save(char)
        store.load_all()

        # Update description but not name
        char.description = "Updated description"
        store.save(char)

        # Index should still have the UUID mapped to same slug
        assert char.uuid in store._uuid_index
        assert store._uuid_index[char.uuid] == "test-character"

    def test_given_character_name_changed_when_saved_then_old_file_removed(
        self, tmp_path
    ):
        """Given a character's name changes from 'Alice' to 'Alicia', when save() is called, then the old file 'alice.yaml' is removed."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="Alice",
            description="Original name",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Story",
        )
        store.save(char)
        store.load_all()

        old_path = tmp_path / "alice.yaml"
        assert old_path.exists()

        # Change the name
        char.name = "Alicia"
        store.save(char)

        # Old file should be removed
        assert not old_path.exists()

    def test_given_character_name_changed_when_saved_then_new_file_created(
        self, tmp_path
    ):
        """Given a character's name changes, when save() is called, then a new file with the new slug is created."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="Alice",
            description="Original name",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Story",
        )
        store.save(char)
        store.load_all()

        # Change the name
        char.name = "Alicia"
        store.save(char)

        # New file should exist
        new_path = tmp_path / "alicia.yaml"
        assert new_path.exists()

    def test_given_character_name_changed_when_saved_then_uuid_preserved(
        self, tmp_path
    ):
        """Given a character's name changes, when save() is called, then the UUID remains the same."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="Alice",
            description="Original name",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Story",
        )
        store.save(char)
        store.load_all()

        original_uuid = char.uuid

        # Change the name
        char.name = "Alicia"
        store.save(char)

        # UUID should be preserved
        assert char.uuid == original_uuid

        # Load the character and verify UUID
        loaded = store.load("Alicia")
        assert loaded.uuid == original_uuid

    def test_given_character_name_changed_when_saved_then_index_updated_with_new_slug(
        self, tmp_path
    ):
        """Given a character's name changes, when save() is called, then the UUID index maps the UUID to the new slug."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="Alice",
            description="Original name",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Story",
        )
        store.save(char)
        store.load_all()

        uuid_before = char.uuid

        # Change the name
        char.name = "Alicia"
        store.save(char)

        # Index should map UUID to new slug
        assert uuid_before in store._uuid_index
        assert store._uuid_index[uuid_before] == "alicia"
