"""Unit tests for CharacterStore.load_all method."""

from __future__ import annotations

from character_store.store import CharacterStore
from models import CharacterProfile


class TestCharacterStoreLoadAll:
    """Tests for CharacterStore.load_all()."""

    def test_given_library_with_multiple_characters_when_load_all_called_then_all_characters_returned(
        self, tmp_path
    ):
        """Given a library with 3 character YAML files, when load_all() is called, then a list of 3 CharacterProfile objects is returned."""
        store = CharacterStore(library_dir=tmp_path)

        # Create and save 3 characters
        char1 = CharacterProfile(
            name="Alice Wonder",
            description="Curious explorer",
            role="protagonist",
            motivations="Discover the unknown",
            relationships="Friends with Bob",
            backstory="Always asking questions",
        )
        char2 = CharacterProfile(
            name="Bob Builder",
            description="Practical engineer",
            role="supporting",
            motivations="Build things",
            relationships="Helps Alice",
            backstory="Grew up building",
        )
        char3 = CharacterProfile(
            name="Charlie Chaplin",
            description="Silent comedian",
            role="antagonist",
            motivations="Make people laugh",
            relationships="Rivals with Alice",
            backstory="Born performer",
        )

        store.save(char1)
        store.save(char2)
        store.save(char3)

        # Load all characters
        all_chars = store.load_all()

        assert len(all_chars) == 3
        names = {char.name for char in all_chars}
        assert names == {"Alice Wonder", "Bob Builder", "Charlie Chaplin"}

    def test_given_empty_library_when_load_all_called_then_empty_list_returned(
        self, tmp_path
    ):
        """Given an empty library directory, when load_all() is called, then an empty list is returned."""
        # Create empty library directory
        tmp_path.mkdir(exist_ok=True)
        store = CharacterStore(library_dir=tmp_path)

        all_chars = store.load_all()

        assert all_chars == []

    def test_given_library_with_characters_when_load_all_called_then_uuid_to_slug_index_built(
        self, tmp_path
    ):
        """Given a library with characters, when load_all() is called, then an internal UUID-to-slug index is created mapping each character's UUID to its slug."""
        store = CharacterStore(library_dir=tmp_path)

        char1 = CharacterProfile(
            name="Test Character",
            description="A test",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Test backstory",
        )
        store.save(char1)

        # Load all to build index
        store.load_all()

        # Check that the internal index was built
        assert hasattr(store, "_uuid_index")
        assert char1.uuid in store._uuid_index
        assert store._uuid_index[char1.uuid] == "test-character"

    def test_given_nonexistent_library_dir_when_load_all_called_then_empty_list_returned(
        self, tmp_path
    ):
        """Given a library directory that does not exist, when load_all() is called, then an empty list is returned."""
        nonexistent_dir = tmp_path / "does_not_exist"
        store = CharacterStore(library_dir=nonexistent_dir)

        all_chars = store.load_all()

        assert all_chars == []

    def test_given_library_with_characters_when_load_all_called_then_characters_have_correct_data(
        self, tmp_path
    ):
        """Given saved characters in the library, when load_all() is called, then the returned CharacterProfile objects have correct field values."""
        store = CharacterStore(library_dir=tmp_path)

        original = CharacterProfile(
            name="Detailed Character",
            description="Very detailed",
            role="protagonist",
            motivations="Win the day",
            relationships="Allied with heroes",
            backstory="Long and complex backstory",
        )
        store.save(original)

        all_chars = store.load_all()

        assert len(all_chars) == 1
        loaded = all_chars[0]
        assert loaded.name == original.name
        assert loaded.description == original.description
        assert loaded.role == original.role
        assert loaded.motivations == original.motivations
        assert loaded.relationships == original.relationships
        assert loaded.backstory == original.backstory
        assert loaded.uuid == original.uuid
