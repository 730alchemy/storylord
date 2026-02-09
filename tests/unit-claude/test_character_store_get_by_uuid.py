"""Unit tests for CharacterStore.get_by_uuid method."""

from __future__ import annotations

import pytest

from character_store.store import CharacterStore
from models import CharacterProfile


class TestCharacterStoreGetByUUID:
    """Tests for CharacterStore.get_by_uuid()."""

    def test_given_valid_uuid_when_get_by_uuid_called_then_character_returned(
        self, tmp_path
    ):
        """Given a populated UUID index with a valid UUID, when get_by_uuid() is called, then the corresponding CharacterProfile is returned."""
        store = CharacterStore(library_dir=tmp_path)

        char = CharacterProfile(
            name="Test Character",
            description="A test character",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Test backstory",
        )
        store.save(char)
        store.load_all()  # Build the UUID index

        loaded = store.get_by_uuid(char.uuid)

        assert loaded.name == "Test Character"
        assert loaded.uuid == char.uuid

    def test_given_nonexistent_uuid_when_get_by_uuid_called_then_raises_KeyError(
        self, tmp_path
    ):
        """Given a UUID that does not exist in the index, when get_by_uuid() is called, then a KeyError is raised."""
        store = CharacterStore(library_dir=tmp_path)
        store.load_all()  # Build empty index

        with pytest.raises(KeyError):
            store.get_by_uuid("nonexistent-uuid")

    def test_given_multiple_characters_when_get_by_uuid_called_then_correct_character_returned(
        self, tmp_path
    ):
        """Given multiple characters in the library, when get_by_uuid() is called with a specific UUID, then the correct CharacterProfile is returned."""
        store = CharacterStore(library_dir=tmp_path)

        char1 = CharacterProfile(
            name="Alice",
            description="First character",
            role="protagonist",
            motivations="Win",
            relationships="Friends with Bob",
            backstory="Alice's story",
        )
        char2 = CharacterProfile(
            name="Bob",
            description="Second character",
            role="supporting",
            motivations="Help Alice",
            relationships="Friends with Alice",
            backstory="Bob's story",
        )
        char3 = CharacterProfile(
            name="Charlie",
            description="Third character",
            role="antagonist",
            motivations="Oppose Alice",
            relationships="Rivals",
            backstory="Charlie's story",
        )

        store.save(char1)
        store.save(char2)
        store.save(char3)
        store.load_all()

        # Load char2 by UUID
        loaded = store.get_by_uuid(char2.uuid)

        assert loaded.name == "Bob"
        assert loaded.uuid == char2.uuid
        assert loaded.description == "Second character"

    def test_given_get_by_uuid_called_then_returned_profile_has_correct_data(
        self, tmp_path
    ):
        """Given a character in the library, when get_by_uuid() is called, then the returned CharacterProfile has all correct field values."""
        store = CharacterStore(library_dir=tmp_path)

        original = CharacterProfile(
            name="Detailed Character",
            description="Very detailed description",
            role="protagonist",
            motivations="Complex motivations",
            relationships="Many relationships",
            backstory="Long backstory",
        )
        store.save(original)
        store.load_all()

        loaded = store.get_by_uuid(original.uuid)

        assert loaded.name == original.name
        assert loaded.description == original.description
        assert loaded.role == original.role
        assert loaded.motivations == original.motivations
        assert loaded.relationships == original.relationships
        assert loaded.backstory == original.backstory
        assert loaded.uuid == original.uuid
