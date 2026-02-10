"""Unit tests for GET /api/v1/characters endpoint."""

from __future__ import annotations


import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from character_store.store import CharacterStore
from models import CharacterProfile


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def override_character_store(tmp_path, test_app):
    """Override the character store dependency with a test store."""
    from api.dependencies import get_character_store

    def _get_test_store():
        store = CharacterStore(library_dir=tmp_path)
        store.load_all()
        return store

    test_app.dependency_overrides[get_character_store] = _get_test_store
    return tmp_path


class TestListCharacters:
    """Tests for GET /api/v1/characters endpoint."""

    def test_given_multiple_characters_when_get_characters_then_all_returned(
        self, client, override_character_store
    ):
        """Given 3 characters in the library, when GET /api/v1/characters is called, then a 200 response with JSON array of 3 characters is returned."""
        # Create test characters
        store = CharacterStore(library_dir=override_character_store)
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

        response = client.get("/api/v1/characters")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        names = {char["name"] for char in data}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_given_empty_library_when_get_characters_then_empty_array_returned(
        self, client, override_character_store
    ):
        """Given an empty library, when GET /api/v1/characters is called, then a 200 response with empty JSON array is returned."""
        response = client.get("/api/v1/characters")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_given_characters_when_get_characters_then_uuids_included(
        self, client, override_character_store
    ):
        """Given characters in the library, when GET /api/v1/characters is called, then each character object includes its uuid field."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Test Character",
            description="Test",
            role="protagonist",
            motivations="Test",
            relationships="None",
            backstory="Test",
        )
        store.save(char)

        response = client.get("/api/v1/characters")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "uuid" in data[0]
        assert data[0]["uuid"] == char.uuid
