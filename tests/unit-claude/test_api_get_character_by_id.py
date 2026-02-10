"""Unit tests for GET /api/v1/characters/{id} endpoint."""

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


class TestGetCharacterById:
    """Tests for GET /api/v1/characters/{id} endpoint."""

    def test_given_valid_uuid_when_get_character_by_id_then_character_returned(
        self, client, override_character_store
    ):
        """Given a character with UUID exists, when GET /api/v1/characters/{id} is called, then a 200 response with the full CharacterProfile is returned."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Test Character",
            description="A test character",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Test backstory",
        )
        store.save(char)

        response = client.get(f"/api/v1/characters/{char.uuid}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Character"
        assert data["description"] == "A test character"

    def test_given_nonexistent_uuid_when_get_character_by_id_then_404_returned(
        self, client, override_character_store
    ):
        """Given no character with UUID exists, when GET /api/v1/characters/{id} is called, then a 404 response is returned."""
        response = client.get("/api/v1/characters/nonexistent-uuid")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_given_valid_uuid_when_get_character_by_id_then_uuid_included(
        self, client, override_character_store
    ):
        """Given a character exists, when GET /api/v1/characters/{id} is called, then the response includes the uuid field."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Test Character",
            description="A test character",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Test backstory",
        )
        store.save(char)

        response = client.get(f"/api/v1/characters/{char.uuid}")

        assert response.status_code == 200
        data = response.json()
        assert "uuid" in data
        assert data["uuid"] == char.uuid
