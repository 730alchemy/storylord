"""Character resource endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.dependencies import get_character_store
from api.schemas import CharacterCreate
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


@router.post("/", response_model=CharacterProfile, status_code=status.HTTP_201_CREATED)
async def create_character(
    request: Request,
    character_data: CharacterCreate,
    store: CharacterStore = Depends(get_character_store),
) -> CharacterProfile:
    """Create a new character.

    Args:
        request: The FastAPI request object.
        character_data: The character data (validated against CharacterCreate schema).
        store: The character store.

    Returns:
        The created CharacterProfile with auto-generated UUID.

    Raises:
        HTTPException: 422 if uuid is provided in request body.
    """
    # Check raw body for uuid field
    body = await request.json()
    if "uuid" in body:
        raise HTTPException(
            status_code=422,
            detail="uuid must not be provided on creation",
        )

    # Create CharacterProfile (auto-generates UUID)
    profile = CharacterProfile(
        name=character_data.name,
        description=character_data.description,
        role=character_data.role,
        motivations=character_data.motivations,
        relationships=character_data.relationships,
        backstory=character_data.backstory,
        agent_config=character_data.agent_config,
    )

    # Save to store
    store.save(profile)

    return profile
