"""Unit tests for PUT /api/v1/characters/{id} endpoint."""

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


class TestUpdateCharacter:
    """Tests for PUT /api/v1/characters/{id} endpoint."""

    def test_given_valid_uuid_and_data_when_put_then_200_with_updated_character(
        self, client, override_character_store
    ):
        """Given valid UUID and CharacterUpdate data, when PUT is called, then 200 with updated character is returned."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Original Name",
            description="Original description",
            role="protagonist",
            motivations="Original motivations",
            relationships="Original relationships",
            backstory="Original backstory",
        )
        store.save(char)

        updated_data = {
            "name": "Original Name",  # Keep same name
            "description": "Updated description",
            "role": "antagonist",
            "motivations": "Updated motivations",
            "relationships": "Updated relationships",
            "backstory": "Updated backstory",
        }

        response = client.put(f"/api/v1/characters/{char.uuid}", json=updated_data)

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["role"] == "antagonist"

    def test_given_name_change_when_put_then_old_file_removed_new_file_created(
        self, client, override_character_store
    ):
        """Given PUT changes character name, when processed, then old file is removed and new file is created."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Old Name",
            description="Description",
            role="protagonist",
            motivations="Motivations",
            relationships="Relationships",
            backstory="Backstory",
        )
        store.save(char)

        old_path = override_character_store / "old-name.yaml"
        assert old_path.exists()

        updated_data = {
            "name": "New Name",
            "description": "Description",
            "role": "protagonist",
            "motivations": "Motivations",
            "relationships": "Relationships",
            "backstory": "Backstory",
        }

        response = client.put(f"/api/v1/characters/{char.uuid}", json=updated_data)

        assert response.status_code == 200
        assert not old_path.exists()
        new_path = override_character_store / "new-name.yaml"
        assert new_path.exists()

    def test_given_name_change_when_put_then_uuid_preserved(
        self, client, override_character_store
    ):
        """Given PUT changes character name, when processed, then UUID remains the same."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Old Name",
            description="Description",
            role="protagonist",
            motivations="Motivations",
            relationships="Relationships",
            backstory="Backstory",
        )
        store.save(char)
        original_uuid = char.uuid

        updated_data = {
            "name": "New Name",
            "description": "Description",
            "role": "protagonist",
            "motivations": "Motivations",
            "relationships": "Relationships",
            "backstory": "Backstory",
        }

        response = client.put(f"/api/v1/characters/{char.uuid}", json=updated_data)

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == original_uuid

    def test_given_nonexistent_uuid_when_put_then_404_returned(
        self, client, override_character_store
    ):
        """Given PUT to nonexistent UUID, when called, then 404 is returned."""
        updated_data = {
            "name": "Some Name",
            "description": "Description",
            "role": "protagonist",
            "motivations": "Motivations",
            "relationships": "Relationships",
            "backstory": "Backstory",
        }

        response = client.put("/api/v1/characters/nonexistent-uuid", json=updated_data)

        assert response.status_code == 404

    def test_given_missing_fields_when_put_then_422_returned(
        self, client, override_character_store
    ):
        """Given PUT with missing required fields, when called, then 422 is returned."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Test",
            description="Description",
            role="protagonist",
            motivations="Motivations",
            relationships="Relationships",
            backstory="Backstory",
        )
        store.save(char)

        incomplete_data = {
            "name": "Updated Name",
            # Missing description, role, motivations, relationships, backstory
        }

        response = client.put(f"/api/v1/characters/{char.uuid}", json=incomplete_data)

        assert response.status_code == 422

    def test_given_uuid_in_body_when_put_then_path_uuid_takes_precedence(
        self, client, override_character_store
    ):
        """Given PUT body includes different uuid, when processed, then path parameter UUID is used."""
        store = CharacterStore(library_dir=override_character_store)
        char = CharacterProfile(
            name="Test Character",
            description="Description",
            role="protagonist",
            motivations="Motivations",
            relationships="Relationships",
            backstory="Backstory",
        )
        store.save(char)

        updated_data = {
            "uuid": "some-other-uuid",  # This should be ignored
            "name": "Updated Name",
            "description": "Updated description",
            "role": "antagonist",
            "motivations": "Updated motivations",
            "relationships": "Updated relationships",
            "backstory": "Updated backstory",
        }

        response = client.put(f"/api/v1/characters/{char.uuid}", json=updated_data)

        assert response.status_code == 200
        data = response.json()
        # UUID should be from path, not body
        assert data["uuid"] == char.uuid
        assert data["uuid"] != "some-other-uuid"
