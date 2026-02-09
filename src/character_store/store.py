"""Character library store for persisting and loading CharacterProfile objects."""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml

from character_store.slugify import slugify_name
from models import CharacterProfile

log = structlog.get_logger(__name__)


class CharacterStore:
    """Persists and loads CharacterProfile objects as YAML files in a local directory."""

    def __init__(self, library_dir: Path):
        self._library_dir = library_dir
        self._uuid_index: dict[str, str] = {}  # Maps UUID to slug

    def save(self, profile: CharacterProfile) -> Path:
        """Save a CharacterProfile to the library as a YAML file.

        If the character's name has changed (resulting in a different slug),
        the old file is removed. If a file already exists at the new path,
        a backup is created with a .old extension before overwriting.

        Args:
            profile: The character profile to persist.

        Returns:
            The path to the written YAML file.
        """
        self._library_dir.mkdir(parents=True, exist_ok=True)

        new_slug = slugify_name(profile.name)
        new_path = self._library_dir / f"{new_slug}.yaml"

        # Check if this is a rename (character with same UUID, different slug)
        if profile.uuid in self._uuid_index:
            old_slug = self._uuid_index[profile.uuid]
            if old_slug != new_slug:
                # Name changed - remove old file
                old_path = self._library_dir / f"{old_slug}.yaml"
                if old_path.exists():
                    old_path.unlink()
                    log.info(
                        "character_renamed",
                        uuid=profile.uuid,
                        old_slug=old_slug,
                        new_slug=new_slug,
                    )

        # Handle overwrite of existing file at new path
        if new_path.exists():
            backup = new_path.with_suffix(".yaml.old")
            backup.write_text(new_path.read_text())
            log.warning(
                "character_file_overwritten",
                character=profile.name,
                backup=str(backup),
            )

        # Write the file
        data = profile.model_dump(mode="json", exclude_none=True)
        new_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

        # Update the UUID index
        self._uuid_index[profile.uuid] = new_slug

        return new_path

    def load(self, name: str) -> CharacterProfile:
        """Load a CharacterProfile from the library by character name.

        If the file lacks a UUID, one is auto-generated and the file is
        immediately rewritten with the UUID persisted.

        Args:
            name: The character's name. Slugified internally to resolve
                  the filename.

        Returns:
            The deserialized and validated CharacterProfile.

        Raises:
            FileNotFoundError: If no file exists for the given name.
            pydantic.ValidationError: If the file content doesn't match
                the CharacterProfile schema.
        """
        path = self._library_dir / f"{slugify_name(name)}.yaml"

        if not path.exists():
            raise FileNotFoundError(
                f"Character '{name}' not found. Expected file: {path}"
            )

        data = yaml.safe_load(path.read_text())
        profile = CharacterProfile.model_validate(data)

        # UUID migration: if file didn't have UUID, persist it now
        if "uuid" not in data:
            log.info(
                "uuid_migration",
                character=name,
                uuid=profile.uuid,
                message="Auto-assigned UUID to legacy character file",
            )
            # Rewrite the file with UUID
            updated_data = profile.model_dump(mode="json", exclude_none=True)
            path.write_text(
                yaml.dump(updated_data, default_flow_style=False, sort_keys=False)
            )

        # Update UUID index if it exists
        if self._uuid_index is not None:
            slug = path.stem
            self._uuid_index[profile.uuid] = slug

        return profile

    def exists(self, name: str) -> bool:
        """Check whether a character exists in the library.

        Args:
            name: The character's name. Slugified internally to resolve
                  the filename.

        Returns:
            True if the character's YAML file exists, False otherwise.
        """
        if not self._library_dir.exists():
            return False
        path = self._library_dir / f"{slugify_name(name)}.yaml"
        return path.exists()

    def list_names(self) -> list[str]:
        """List all character slugified names in the library.

        Returns:
            A list of slugified character names (the YAML filenames
            without the .yaml extension). Returns an empty list if the
            library directory does not exist.
        """
        if not self._library_dir.exists():
            return []
        return [p.stem for p in sorted(self._library_dir.glob("*.yaml"))]

    def load_all(self) -> list[CharacterProfile]:
        """Load all characters from the library and build UUID index.

        Scans all YAML files in the library directory, loads each as a
        CharacterProfile, and builds an in-memory index mapping UUIDs
        to slugs for fast UUID-based lookups.

        Returns:
            A list of all CharacterProfile objects in the library.
            Returns an empty list if the library directory does not exist.
        """
        if not self._library_dir.exists():
            return []

        characters = []
        self._uuid_index.clear()

        for yaml_path in sorted(self._library_dir.glob("*.yaml")):
            data = yaml.safe_load(yaml_path.read_text())
            profile = CharacterProfile.model_validate(data)
            characters.append(profile)

            # Build UUID-to-slug index
            slug = yaml_path.stem
            self._uuid_index[profile.uuid] = slug

        return characters

    def get_by_uuid(self, character_uuid: str) -> CharacterProfile:
        """Load a CharacterProfile by UUID.

        Args:
            character_uuid: The UUID of the character to load.

        Returns:
            The deserialized and validated CharacterProfile.

        Raises:
            KeyError: If no character with the given UUID exists in the index.
        """
        if character_uuid not in self._uuid_index:
            raise KeyError(f"Character with UUID '{character_uuid}' not found in index")

        slug = self._uuid_index[character_uuid]
        # Load by the slug name (which will also handle UUID migration if needed)
        path = self._library_dir / f"{slug}.yaml"
        data = yaml.safe_load(path.read_text())
        return CharacterProfile.model_validate(data)

    def delete(self, character_uuid: str) -> None:
        """Delete a character by UUID.

        Removes the character's YAML file from disk and removes the UUID
        from the in-memory index.

        Args:
            character_uuid: The UUID of the character to delete.

        Raises:
            KeyError: If no character with the given UUID exists in the index.
        """
        if character_uuid not in self._uuid_index:
            raise KeyError(f"Character with UUID '{character_uuid}' not found in index")

        slug = self._uuid_index[character_uuid]
        path = self._library_dir / f"{slug}.yaml"

        # Remove the file
        if path.exists():
            path.unlink()
            log.info("character_deleted", uuid=character_uuid, slug=slug)

        # Remove from index
        del self._uuid_index[character_uuid]
