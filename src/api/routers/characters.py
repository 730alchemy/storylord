"""Character resource endpoints."""

from fastapi import APIRouter, Depends, HTTPException

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


@router.get("/{character_id}", response_model=CharacterProfile)
def get_character(
    character_id: str,
    store: CharacterStore = Depends(get_character_store),
) -> CharacterProfile:
    """Get a character by UUID.

    Args:
        character_id: The UUID of the character to retrieve.

    Returns:
        The CharacterProfile for the given UUID.

    Raises:
        HTTPException: 404 if character not found.
    """
    try:
        return store.get_by_uuid(character_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Character with UUID '{character_id}' not found",
        )
