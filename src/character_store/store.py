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
