# Specification: Characters REST API

## Objective

Expose the character library as a RESTful API using FastAPI, enabling full CRUD operations (Create, Read, Update, Delete -- no PATCH) on `CharacterProfile` resources identified by UUID. This API will serve as the backend for a future web UI and other programmatic consumers. Characters continue to be stored as YAML files on disk via the existing `CharacterStore`, with UUIDs added to `CharacterProfile` and an in-memory index for UUID-to-slug resolution.

---

## Constraints

### Technical
- FastAPI as the web framework, uvicorn as the ASGI server
- Integrate with the existing `CharacterStore` (YAML-on-disk) in `src/character_store/store.py`
- Add `uuid` field to `CharacterProfile` in `src/models.py`
- Python 3.13, PDM for dependency management
- Must not break existing functionality: Slack bot character creation, Storylord pipeline's `load_input_node`, `character_library` resolution

### Scope
- CRUD minus PATCH (GET list, GET by ID, POST, PUT, DELETE)
- No authentication or authorization
- No pagination on the list endpoint
- No filtering or search on the list endpoint
- No rate limiting
- Characters resource only -- no other resources

### Quality
- Automated tests using pytest (consistent with existing test suite in `tests/`)
- API responses follow standard REST conventions (proper status codes, JSON responses)
- Input validation via Pydantic (FastAPI's native approach)

### Compatibility
- Adding `uuid` to `CharacterProfile` must be backward-compatible: existing YAML files without a UUID are auto-assigned one on load and persisted immediately
- Existing `CharacterStore.save()` / `load()` / `list_names()` callers (Slack bot, `load_input_node`) continue to work
- `character_library` field on `StoryInput` resolves by slugified name (not UUID) -- unchanged
- `list_names()` does not trigger UUID migration; only `load()` and `load_all()` do

---

## Acceptance Criteria

### Model Changes (UUID on CharacterProfile)

1. **AC-1**: Given a `CharacterProfile` is instantiated without providing a `uuid` field, when the object is created, then a UUID v4 string is auto-generated and assigned to the `uuid` field.

2. **AC-2**: Given a `CharacterProfile` is instantiated with an explicit `uuid` value, when the object is created, then the provided UUID is used (not overwritten).

3. **AC-3**: Given an existing YAML file in the character library that has no `uuid` field, when `CharacterStore.load()` reads it, then a UUID is auto-assigned and the file is immediately rewritten with the UUID persisted.

4. **AC-4**: Given an existing YAML file that already contains a `uuid` field, when `CharacterStore.load()` reads it, then the existing UUID is preserved and the file is not rewritten.

### CharacterStore Changes (UUID Index)

5. **AC-5**: Given a `CharacterStore` instance, when `load_all()` is called, then all character YAML files are loaded and an in-memory index mapping UUID to slug is built.

6. **AC-6**: Given a populated UUID index, when `get_by_uuid(uuid)` is called with a valid UUID, then the corresponding `CharacterProfile` is returned.

7. **AC-7**: Given a populated UUID index, when `get_by_uuid(uuid)` is called with a UUID that does not exist, then a `KeyError` is raised.

8. **AC-8**: Given a character is saved via `save(profile)`, when the save completes, then the UUID-to-slug index is updated to reflect the current slug for that UUID.

9. **AC-9**: Given a character whose name has changed (new slug), when `save(profile)` is called, then the old YAML file is removed, the new file is written, and the index is updated.

### API: List Characters (GET /api/v1/characters)

10. **AC-10**: Given the character library contains 3 characters, when `GET /api/v1/characters` is called, then a 200 response is returned with a JSON array of 3 full `CharacterProfile` objects, each including its `uuid`.

11. **AC-11**: Given the character library is empty, when `GET /api/v1/characters` is called, then a 200 response is returned with an empty JSON array.

### API: Get Character (GET /api/v1/characters/{id})

12. **AC-12**: Given a character with UUID `abc-123` exists, when `GET /api/v1/characters/abc-123` is called, then a 200 response is returned with the full `CharacterProfile` JSON including `uuid`.

13. **AC-13**: Given no character with UUID `nonexistent` exists, when `GET /api/v1/characters/nonexistent` is called, then a 404 response is returned with a JSON body containing an error message.

### API: Create Character (POST /api/v1/characters)

14. **AC-14**: Given a valid `CharacterProfile` JSON body (without `uuid`), when `POST /api/v1/characters` is called, then a 201 response is returned with the created character including an auto-generated `uuid`, and the character YAML file is written to disk.

15. **AC-15**: Given a JSON body missing required fields (e.g., no `name`), when `POST /api/v1/characters` is called, then a 422 response is returned with field-level validation errors.

16. **AC-16**: Given a JSON body that includes a `uuid` field, when `POST /api/v1/characters` is called, then a 422 response is returned with an error message indicating that `uuid` must not be provided on creation.

### API: Update Character (PUT /api/v1/characters/{id})

17. **AC-17**: Given a character with UUID `abc-123` exists, when `PUT /api/v1/characters/abc-123` is called with a valid full `CharacterProfile` JSON body, then a 200 response is returned with the updated character, and the YAML file is updated on disk.

18. **AC-18**: Given a PUT request changes the character's name from "Elijah Boondog" to "Elijah Bonfire", when processed, then the old file `elijah-boondog.yaml` is removed, `elijah-bonfire.yaml` is written, and the UUID remains `abc-123`.

19. **AC-19**: Given no character with UUID `nonexistent` exists, when `PUT /api/v1/characters/nonexistent` is called, then a 404 response is returned.

20. **AC-20**: Given a PUT request body missing required fields, when `PUT /api/v1/characters/{id}` is called, then a 422 response is returned with field-level validation errors.

21. **AC-21**: Given a PUT request body includes a `uuid` field that differs from the path parameter, when processed, then the path parameter UUID takes precedence (body UUID is ignored).

### API: Delete Character (DELETE /api/v1/characters/{id})

22. **AC-22**: Given a character with UUID `abc-123` exists, when `DELETE /api/v1/characters/abc-123` is called, then a 204 response is returned with no body, the YAML file is permanently removed from disk, and the UUID is removed from the index.

23. **AC-23**: Given no character with UUID `nonexistent` exists, when `DELETE /api/v1/characters/nonexistent` is called, then a 404 response is returned.

### Backward Compatibility

24. **AC-24**: Given a `StoryInput` YAML with `character_library: ["elijah-boondog"]`, when `load_input_node` executes, then the character is loaded by slug name as before (UUID presence in the file does not affect slug-based resolution).

25. **AC-25**: Given the Slack bot calls `CharacterStore.save(profile)` where the profile has an auto-generated UUID, when saved, then the YAML file includes the UUID and the Slack bot flow is otherwise unaffected.

---

## Dependencies (New Packages)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | `>=0.115.0` | Web framework for REST API |
| `uvicorn` | `>=0.34.0` | ASGI server to run the FastAPI app |

---

## File Layout

```
src/
  api/
    __init__.py              # Package init, exports create_app() and main()
    app.py                   # FastAPI app setup, lifespan, router inclusion
    routers/
      __init__.py
      characters.py          # /api/v1/characters endpoints
    schemas.py               # Request/response schemas (CharacterCreate, etc.)
    dependencies.py          # FastAPI dependencies (CharacterStore provider)
  character_store/
    store.py                 # (existing) Add load_all(), get_by_uuid(), delete(), UUID index
    slugify.py               # (existing) Unchanged
  models.py                  # (existing) Add uuid field to CharacterProfile
  config.py                  # (existing) Add API server settings (host, port)
```

---

## Configuration

Add to `src/config.py` `Settings` class:

```python
# API server
api_host: str = "127.0.0.1"
api_port: int = 8000
```

Add to `pyproject.toml`:

```toml
[project.scripts]
storylord-api = "api:main"

[tool.pdm.scripts]
api = "uvicorn api.app:app --reload"
```

---

## Key Interfaces

### CharacterStore (Enhanced)

```python
class CharacterStore:
    # Existing methods (unchanged signatures)
    def save(self, profile: CharacterProfile) -> Path: ...
    def load(self, name: str) -> CharacterProfile: ...
    def exists(self, name: str) -> bool: ...
    def list_names(self) -> list[str]: ...

    # New methods
    def load_all(self) -> list[CharacterProfile]:
        """Load all characters, build UUID-to-slug index, migrate legacy files."""

    def get_by_uuid(self, uuid: str) -> CharacterProfile:
        """Load character by UUID. Raises KeyError if not found."""

    def delete(self, uuid: str) -> None:
        """Delete character by UUID. Raises KeyError if not found."""
```

### Request Schemas

```python
class CharacterCreate(BaseModel):
    """Request body for POST /api/v1/characters. UUID must not be provided."""
    name: str
    description: str
    role: str
    motivations: str
    relationships: str
    backstory: str
    agent_config: CharacterAgentConfig | None = None

class CharacterUpdate(BaseModel):
    """Request body for PUT /api/v1/characters/{id}. UUID in body is ignored."""
    name: str
    description: str
    role: str
    motivations: str
    relationships: str
    backstory: str
    agent_config: CharacterAgentConfig | None = None
```

---

## PR/Commit Slices

### Slice 1: Add UUID to CharacterProfile

- **Description**: Add an auto-generated UUID field to `CharacterProfile` in `models.py`. This is the foundational schema change that all subsequent slices depend on.
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Complexity**: S
- **Dependencies**: None
- **Commits**:
  1. Add `uuid` field to `CharacterProfile` with `default_factory=uuid4`, serialized as string

### Slice 2: CharacterStore UUID Support

- **Description**: Enhance `CharacterStore` with UUID-based indexing, `load_all()`, `get_by_uuid()`, UUID migration for legacy files, `delete()` capability, and rename-on-save when the character name changes.
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9
- **Complexity**: M
- **Dependencies**: Slice 1
- **Commits**:
  1. Add `load_all()` method that scans all YAML files and builds an in-memory UUID-to-slug index
  2. Add UUID migration logic to `load()` -- auto-assign and persist UUID for legacy files, skip rewrite if UUID already present
  3. Add `get_by_uuid()` method using the index
  4. Add `delete()` method that removes the YAML file and index entry
  5. Modify `save()` to handle name changes (remove old file, write new file, update index)

### Slice 3: FastAPI App Skeleton and List/Get Endpoints

- **Description**: Introduce FastAPI as a dependency, create the app skeleton with router structure, and implement the read-only endpoints (GET list, GET by ID).
- **Acceptance Criteria Addressed**: AC-10, AC-11, AC-12, AC-13
- **Complexity**: M
- **Dependencies**: Slice 2
- **Commits**:
  1. Add `fastapi` and `uvicorn` to project dependencies
  2. Create FastAPI app skeleton with `/api/v1` router prefix, `CharacterStore` dependency, entry point script, and PDM dev script
  3. Implement `GET /api/v1/characters` (list all)
  4. Implement `GET /api/v1/characters/{id}` (get by UUID)

### Slice 4: POST and PUT Endpoints

- **Description**: Implement the create and update endpoints with full validation, including UUID rejection on POST and name-change handling on PUT.
- **Acceptance Criteria Addressed**: AC-14, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20, AC-21
- **Complexity**: M
- **Dependencies**: Slice 3
- **Commits**:
  1. Define request body schemas (`CharacterCreate`, `CharacterUpdate`) that exclude `uuid`
  2. Implement `POST /api/v1/characters` with UUID auto-generation and reject-if-UUID-present logic
  3. Implement `PUT /api/v1/characters/{id}` with full replacement semantics and name-change support

### Slice 5: DELETE Endpoint and Backward Compatibility Verification

- **Description**: Implement the delete endpoint and add integration tests verifying that the Slack bot flow and `load_input_node` pipeline remain unaffected by the UUID addition.
- **Acceptance Criteria Addressed**: AC-22, AC-23, AC-24, AC-25
- **Complexity**: S
- **Dependencies**: Slice 4
- **Commits**:
  1. Implement `DELETE /api/v1/characters/{id}`
  2. Add backward compatibility tests for `load_input_node` with UUID-bearing YAML files
  3. Add backward compatibility tests for Slack bot `CharacterStore.save()` with UUID

---

## Synchronization Notes

### Must Stay in Sync

1. **CharacterProfile model and YAML serialization**: Both `CharacterStore.save()` and the API responses serialize `CharacterProfile`. The store uses `profile.model_dump(mode='json', exclude_none=True)` for YAML; FastAPI uses Pydantic's JSON serialization natively. Both must include `uuid`.

2. **UUID index and disk state**: The in-memory UUID-to-slug index must be updated on every `save()`, `delete()`, and `load_all()`. Any method that modifies disk state must also update the index.

3. **Request schemas and CharacterProfile**: `CharacterCreate` and `CharacterUpdate` must mirror all fields of `CharacterProfile` except `uuid`. If fields are added to `CharacterProfile` in the future, these schemas must be updated.

4. **Slugification in CharacterStore**: Both slug-based resolution (used by `load_input_node` and Slack bot) and UUID-based resolution (used by the API) must use the same `slugify_name()` function for filename generation.

### Testing Considerations

- API endpoint tests should use FastAPI's `TestClient` (backed by httpx)
- `CharacterStore` tests should use temporary directories via `tmp_path` fixture
- Backward compatibility tests should create YAML files both with and without UUIDs
- UUID migration tests should verify file contents before and after load

---

## Error Handling Strategy

| Error Type | HTTP Status | Handling |
|------------|-------------|----------|
| Character not found by UUID | 404 | JSON body with error message identifying the UUID |
| Validation error (missing/invalid fields) | 422 | FastAPI's default Pydantic validation error response |
| UUID provided on POST | 422 | JSON body with error message: "uuid must not be provided on creation" |
| Unexpected server error | 500 | FastAPI's default error handling, logged via structlog |

---

## Out of Scope (Explicit)

- PATCH endpoint (partial updates)
- Authentication or authorization
- Pagination, filtering, or search
- Rate limiting
- Resources other than characters
- Database storage (future work)
- WebSocket or real-time updates
- OpenAPI customization beyond FastAPI defaults
