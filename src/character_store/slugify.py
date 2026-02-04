"""Slugification for character names to filesystem-safe filenames."""

from __future__ import annotations

from slugify import slugify


def slugify_name(name: str) -> str:
    """Convert a character name to a filesystem-safe slug.

    Args:
        name: The character's name.

    Returns:
        A lowercase, hyphen-separated slug containing only alphanumeric
        characters and hyphens, with no leading or trailing hyphens.

    Raises:
        ValueError: If name is empty or produces an empty slug.
    """
    if not name or not name.strip():
        raise ValueError("Character name must not be empty")

    result = slugify(name)
    if not result:
        raise ValueError(f"Character name '{name}' produced an empty slug")

    return result
