"""Unit tests for CharacterStore.list_names and exists methods."""

from __future__ import annotations

from character_store.store import CharacterStore
from models import CharacterProfile


class TestCharacterStoreListNames:
    """Tests for CharacterStore.list_names()."""

    def test_given_empty_library_when_list_names_called_then_returns_empty_list(
        self, tmp_path
    ):
        """An empty library directory returns no names."""
        store = CharacterStore(library_dir=tmp_path)

        assert store.list_names() == []

    def test_given_multiple_saved_characters_when_list_names_called_then_returns_all_slugified_names(
        self, tmp_path
    ):
        """All saved characters appear in the list as slugified names."""
        store = CharacterStore(library_dir=tmp_path)
        profiles = [
            CharacterProfile(
                name="Elijah Boondog",
                description="First character",
                role="protagonist",
                motivations="Curiosity",
                relationships="",
                backstory="",
            ),
            CharacterProfile(
                name="Jasper Dilsack",
                description="Second character",
                role="antagonist",
                motivations="Ambition",
                relationships="",
                backstory="",
            ),
        ]
        for p in profiles:
            store.save(p)

        names = store.list_names()

        assert sorted(names) == ["elijah-boondog", "jasper-dilsack"]

    def test_given_library_dir_does_not_exist_when_list_names_called_then_returns_empty_list(
        self, tmp_path
    ):
        """A non-existent library directory returns no names rather than raising."""
        store = CharacterStore(library_dir=tmp_path / "nonexistent")

        assert store.list_names() == []


class TestCharacterStoreExists:
    """Tests for CharacterStore.exists()."""

    def test_given_saved_character_when_exists_called_with_that_name_then_returns_True(
        self, tmp_path, sample_profile
    ):
        """exists() returns True for a character that has been saved."""
        store = CharacterStore(library_dir=tmp_path)
        store.save(sample_profile)

        assert store.exists(sample_profile.name) is True

    def test_given_no_saved_character_when_exists_called_then_returns_False(
        self, tmp_path
    ):
        """exists() returns False for a name with no file on disk."""
        store = CharacterStore(library_dir=tmp_path)

        assert store.exists("Nobody Here") is False

    def test_given_library_dir_does_not_exist_when_exists_called_then_returns_False(
        self, tmp_path
    ):
        """A non-existent library directory means no character can exist."""
        store = CharacterStore(library_dir=tmp_path / "nonexistent")

        assert store.exists("Anyone") is False
