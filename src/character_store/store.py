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

    def save(self, profile: CharacterProfile) -> Path:
        """Save a CharacterProfile to the library as a YAML file.

        If a file already exists for this character, a backup is created
        with a .old extension before overwriting.

        Args:
            profile: The character profile to persist.

        Returns:
            The path to the written YAML file.
        """
        self._library_dir.mkdir(parents=True, exist_ok=True)

        path = self._library_dir / f"{slugify_name(profile.name)}.yaml"

        if path.exists():
            backup = path.with_suffix(".yaml.old")
            backup.write_text(path.read_text())
            log.warning(
                "character_file_overwritten",
                character=profile.name,
                backup=str(backup),
            )

        data = profile.model_dump(mode="json", exclude_none=True)
        path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

        return path

    def load(self, name: str) -> CharacterProfile:
        """Load a CharacterProfile from the library by character name.

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
        return CharacterProfile.model_validate(data)

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
