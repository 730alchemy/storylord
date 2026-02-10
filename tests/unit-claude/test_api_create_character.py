"""Unit tests for POST /api/v1/characters endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from character_store.store import CharacterStore


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


class TestCreateCharacter:
    """Tests for POST /api/v1/characters endpoint."""

    def test_given_valid_character_data_when_post_then_201_with_uuid(
        self, client, override_character_store
    ):
        """Given valid CharacterCreate data, when POST is called, then 201 response with character including auto-generated UUID is returned."""
        character_data = {
            "name": "New Character",
            "description": "A new character",
            "role": "protagonist",
            "motivations": "Save the world",
            "relationships": "Friends with everyone",
            "backstory": "Born ready",
        }

        response = client.post("/api/v1/characters", json=character_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Character"
        assert "uuid" in data
        assert data["uuid"] is not None

    def test_given_missing_required_fields_when_post_then_422_returned(
        self, client, override_character_store
    ):
        """Given data missing required fields, when POST is called, then 422 with validation errors is returned."""
        incomplete_data = {
            "name": "Incomplete Character",
            # Missing description, role, motivations, relationships, backstory
        }

        response = client.post("/api/v1/characters", json=incomplete_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_given_uuid_in_body_when_post_then_422_returned(
        self, client, override_character_store
    ):
        """Given data includes uuid field, when POST is called, then 422 with error message is returned."""
        character_data = {
            "uuid": "some-uuid-value",
            "name": "Character With UUID",
            "description": "Should be rejected",
            "role": "protagonist",
            "motivations": "Testing",
            "relationships": "None",
            "backstory": "Testing",
        }

        response = client.post("/api/v1/characters", json=character_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "uuid" in str(data).lower()

    def test_given_valid_post_when_complete_then_character_saved_to_disk(
        self, client, override_character_store
    ):
        """Given valid POST request completes, when checked, then character YAML file exists on disk."""
        character_data = {
            "name": "Saved Character",
            "description": "Will be saved",
            "role": "protagonist",
            "motivations": "Persist",
            "relationships": "None",
            "backstory": "Saved",
        }

        response = client.post("/api/v1/characters", json=character_data)

        assert response.status_code == 201
        yaml_path = override_character_store / "saved-character.yaml"
        assert yaml_path.exists()
