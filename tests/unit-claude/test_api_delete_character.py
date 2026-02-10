"""Unit tests for DELETE /api/v1/characters/{id} endpoint."""

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


class TestDeleteCharacter:
    """Tests for DELETE /api/v1/characters/{id} endpoint."""

    def test_given_valid_uuid_when_delete_then_204_returned(
        self, client, override_character_store
    ):
        """Given valid UUID, when DELETE is called, then 204 with no body is returned."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="To Delete",
            description="Will be deleted",
            role="protagonist",
            motivations="Temporary",
            relationships="None",
            backstory="Short-lived",
        )
        store.save(char)

        response = client.delete(f"/api/v1/characters/{char.uuid}")

        assert response.status_code == 204
        assert response.content == b""

    def test_given_valid_uuid_when_delete_then_file_removed(
        self, client, override_character_store
    ):
        """Given valid UUID, when DELETE completes, then YAML file is removed from disk."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="To Delete",
            description="Will be deleted",
            role="protagonist",
            motivations="Temporary",
            relationships="None",
            backstory="Short-lived",
        )
        store.save(char)

        yaml_path = override_character_store / "to-delete.yaml"
        assert yaml_path.exists()

        response = client.delete(f"/api/v1/characters/{char.uuid}")

        assert response.status_code == 204
        assert not yaml_path.exists()

    def test_given_nonexistent_uuid_when_delete_then_404_returned(
        self, client, override_character_store
    ):
        """Given nonexistent UUID, when DELETE is called, then 404 is returned."""
        response = client.delete("/api/v1/characters/nonexistent-uuid")

        assert response.status_code == 404
