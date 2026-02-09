"""Unit tests for CharacterStore.delete method."""

from __future__ import annotations

import pytest

from character_store.store import CharacterStore
from models import CharacterProfile


class TestCharacterStoreDelete:
    """Tests for CharacterStore.delete()."""

    def test_given_valid_uuid_when_delete_called_then_file_removed(self, tmp_path):
        """Given a character exists, when delete() is called with its UUID, then the YAML file is removed from disk."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="To Be Deleted",
            description="This character will be deleted",
            role="protagonist",
            motivations="None",
            relationships="None",
            backstory="Short",
        )
        store.save(char)
        store.load_all()  # Build index

        yaml_path = tmp_path / "to-be-deleted.yaml"
        assert yaml_path.exists()

        store.delete(char.uuid)

        assert not yaml_path.exists()

    def test_given_valid_uuid_when_delete_called_then_uuid_removed_from_index(
        self, tmp_path
    ):
        """Given a character exists and index is built, when delete() is called, then the UUID is removed from the index."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="To Be Deleted",
            description="This character will be deleted",
            role="protagonist",
            motivations="None",
            relationships="None",
            backstory="Short",
        )
        store.save(char)
        store.load_all()

        assert char.uuid in store._uuid_index

        store.delete(char.uuid)

        assert char.uuid not in store._uuid_index

    def test_given_nonexistent_uuid_when_delete_called_then_raises_KeyError(
        self, tmp_path
    ):
        """Given a UUID that doesn't exist, when delete() is called, then a KeyError is raised."""
        store = CharacterStore(library_dir=tmp_path)
        store.load_all()

        with pytest.raises(KeyError):
            store.delete("nonexistent-uuid")

    def test_given_multiple_characters_when_one_deleted_then_others_remain(
        self, tmp_path
    ):
        """Given multiple characters exist, when one is deleted, then the others remain intact."""
        store = CharacterStore(library_dir=tmp_path)

        char1 = CharacterProfile(
            name="Alice",
            description="First character",
            role="protagonist",
            motivations="Win",
            relationships="None",
            backstory="Alice story",
        )
        char2 = CharacterProfile(
            name="Bob",
            description="Second character",
            role="supporting",
            motivations="Help",
            relationships="None",
            backstory="Bob story",
        )
        char3 = CharacterProfile(
            name="Charlie",
            description="Third character",
            role="antagonist",
            motivations="Oppose",
            relationships="None",
            backstory="Charlie story",
        )

        store.save(char1)
        store.save(char2)
        store.save(char3)
        store.load_all()

        # Delete char2
        store.delete(char2.uuid)

        # Verify char2 is gone
        assert not (tmp_path / "bob.yaml").exists()
        assert char2.uuid not in store._uuid_index

        # Verify char1 and char3 remain
        assert (tmp_path / "alice.yaml").exists()
        assert (tmp_path / "charlie.yaml").exists()
        assert char1.uuid in store._uuid_index
        assert char3.uuid in store._uuid_index
