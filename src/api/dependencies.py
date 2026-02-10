"""FastAPI dependencies for dependency injection."""

from pathlib import Path

from character_store.store import CharacterStore
from config import settings


def get_character_store() -> CharacterStore:
    """Provide a CharacterStore instance for dependency injection.

    Returns:
        CharacterStore instance configured with the library directory from settings.
    """
    library_dir = Path(settings.character_library_dir)
    store = CharacterStore(library_dir=library_dir)
    # Build the UUID index on startup
    store.load_all()
    return store
