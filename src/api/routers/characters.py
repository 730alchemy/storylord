"""Character resource endpoints."""

from fastapi import APIRouter, Depends

from api.dependencies import get_character_store
from character_store.store import CharacterStore
from models import CharacterProfile

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("/", response_model=list[CharacterProfile])
def list_characters(
    store: CharacterStore = Depends(get_character_store),
) -> list[CharacterProfile]:
    """List all characters in the library.

    Returns:
        List of all CharacterProfile objects, each including uuid.
    """
    return store.load_all()
