# Specification: Slack Character Creator for Storylord

## Objective

Enable users to create and persist `CharacterProfile` objects through a conversational Slack bot interface, storing them in a local YAML library that Storylord can consume via a new `character_library` field on `StoryInput`.

---

## Constraints

### Technical
- Must integrate with existing Pydantic models: `CharacterProfile`, `CharacterAgentConfig`
- Must use existing agent type discovery: `discover_character_agent_types()` from `src/agents/discovery.py`
- Must read property schemas from `CharacterAgentType.property_schema` (JSON Schema format)
- Slack app uses Bolt for Python framework
- Python 3.13 (matches existing project)
- No external state store; wizard state lives in memory keyed by `user_id`

### Scope
- Single-workspace Slack app (no OAuth/multi-tenant)
- No character editing after save (only during wizard flow)
- No character deletion from Slack (manual file deletion if needed)
- No character listing/browsing from Slack

### Quality
- All user-facing strings must be clear and conversational
- Modal validation errors must be specific and actionable
- Character YAML files must be valid for direct use in Storylord

### Compatibility
- Existing `StoryInput` YAMLs without `character_library` must continue to work unchanged
- Existing inline `characters` list remains the primary mechanism; library is additive

---

## Acceptance Criteria

### Storylord Integration (Library Resolution)

1. **AC-1**: Given a `StoryInput` YAML with `character_library: ["elijah-boondog", "riley-thorn"]`, when `load_input_node` executes, then the named characters are loaded from the configured library directory and appended to `story_input.characters`.

2. **AC-2**: Given a `StoryInput` YAML without a `character_library` field, when `load_input_node` executes, then behavior is unchanged from current (empty list default, no library loading).

3. **AC-3**: Given a `character_library` entry that references a non-existent file, when `load_input_node` executes, then a clear error is raised identifying the missing character name and expected file path.

4. **AC-4**: Given a character YAML file with an invalid schema (missing required fields, wrong types), when loaded, then Pydantic validation raises an error with field-level details.

### Character Library Store

5. **AC-5**: Given a `CharacterProfile` object, when `CharacterStore.save(profile)` is called, then a YAML file is written to `{library_dir}/{slugified_name}.yaml` containing the serialized profile.

6. **AC-6**: Given a character name "Elijah Boondog", when slugified for filename, then the result is `elijah-boondog.yaml`.

7. **AC-7**: Given a save request for a character whose slugified name matches an existing file, when saved, then the existing file is overwritten (no duplicate detection).

8. **AC-8**: Given a character name with special characters (e.g., "Dr. Smith-Jones III"), when slugified, then only alphanumeric characters and hyphens remain, with no leading/trailing hyphens.

### Slack Wizard: Conversation Flow

9. **AC-9**: Given a user sends `/create-character` in any channel, when the bot receives the command, then it responds with an ephemeral message asking for the character's name and sets user state to `WAITING_NAME`.

10. **AC-10**: Given a user in state `WAITING_NAME` sends a DM to the bot, when the message is received, then the name is captured, state advances to `WAITING_DESCRIPTION`, and bot asks for the description.

11. **AC-11**: Given a user progresses through `WAITING_DESCRIPTION`, `WAITING_MOTIVATIONS`, `WAITING_BACKSTORY`, when each response is received, then state advances and bot asks for the next field.

12. **AC-12**: Given a user in state `WAITING_RELATIONSHIPS` sends "skip" (case-insensitive), when received, then relationships is set to empty string and state advances to `MODAL_1_OPEN`.

13. **AC-13**: Given a user in state `WAITING_RELATIONSHIPS` sends any other text, when received, then relationships is captured and state advances to `MODAL_1_OPEN`.

### Slack Wizard: Modal 1 (Role and Agent Config Toggle)

14. **AC-14**: Given state advances to `MODAL_1_OPEN`, when the bot opens Modal 1, then it contains: (a) a dropdown for `role` with options [protagonist, antagonist, supporting, minor], (b) a toggle for "Enable agent configuration", (c) a dropdown for `agent_type` that is always present but ignored on submission if the toggle is off (Block Kit does not support conditional visibility within a single modal).

15. **AC-15**: Given Modal 1 is open and agent config toggle is off, when user submits, then state advances directly to `PREVIEW` (skipping Modal 2) and `agent_config` is `None`.

16. **AC-16**: Given Modal 1 is open and agent config toggle is on with `agent_type` selected, when user submits, then state advances to `MODAL_2_OPEN` with the selected agent type stored.

17. **AC-17**: Given the `agent_type` dropdown in Modal 1, when rendered, then options are dynamically populated from `discover_character_agent_types()`.

### Slack Wizard: Modal 2 (Agent Properties)

18. **AC-18**: Given state is `MODAL_2_OPEN` with `agent_type="mbti"`, when Modal 2 opens, then it displays 4 numeric input fields (extroversion, intuition, thinking, judging) plus a text area for `agent_instructions`.

19. **AC-19**: Given state is `MODAL_2_OPEN` with `agent_type="default"`, when Modal 2 opens, then it displays 5 numeric input fields (assertiveness, warmth, formality, verbosity, emotionality) plus a text area for `agent_instructions`.

20. **AC-20**: Given Modal 2 numeric inputs, when a user enters a value outside 0-100, then a validation error is shown on that field.

21. **AC-21**: Given Modal 2 is submitted with valid inputs, when processed, then `agent_config` is constructed with the selected type, properties dict, and instructions, and state advances to `PREVIEW`.

### Slack Wizard: Preview

22. **AC-22**: Given state advances to `PREVIEW`, when the bot renders the preview, then it posts an ephemeral message containing the full `CharacterProfile` as a YAML code block.

23. **AC-23**: Given the preview message, when rendered, then it includes two buttons: "Save" and "Edit".

24. **AC-24**: Given user clicks "Edit" on preview, when the correction modal opens, then ALL fields are pre-populated with current values (name, description, motivations, backstory, relationships, role, agent_config toggle). Agent type, properties, and instructions fields are always present; they are pre-populated if agent config is enabled, and ignored on submission if the toggle is off (same Block Kit limitation as Modal 1).

25. **AC-25**: Given user submits the correction modal with changes, when processed, then the preview is re-rendered with updated values (state remains `PREVIEW`).

### Slack Wizard: Save

26. **AC-26**: Given user clicks "Save" on preview, when processed, then `CharacterStore.save()` is called and bot posts an ephemeral confirmation with the file path.

27. **AC-27**: Given save completes successfully, when confirmation is posted, then user state is cleared (or set to `SAVED` then cleared).

### State Management

28. **AC-28**: Given a user has an active wizard session, when the user sends `/create-character` again, then the old session is discarded and a new one begins.

29. **AC-29**: Given a user in any wizard state sends a message that is not a valid response (e.g., an attachment), when processed, then the bot replies with guidance on what input is expected.

---

## Dependencies (New Packages)

| Package | Version | Purpose |
|---------|---------|---------|
| `slack-bolt` | `>=1.18.0` | Slack app framework (Bolt for Python) |
| `python-slugify` | `>=8.0.0` | Consistent filename generation from character names |

---

## File Layout

```
src/
  slack_app/
    __init__.py              # Package init, exports create_app()
    app.py                   # Bolt app setup, event handlers, command handlers
    state.py                 # WizardState dataclass, StateManager (in-memory dict)
    modals.py                # Modal builders: build_modal_1(), build_modal_2(), build_correction_modal()
    handlers/
      __init__.py
      commands.py            # /create-character handler
      messages.py            # DM message handler for freeform fields
      actions.py             # Button click handlers (Save, Edit)
      submissions.py         # Modal submission handlers
    views.py                 # Preview message builder, confirmation message builder
  character_store/
    __init__.py              # Package init, exports CharacterStore
    store.py                 # CharacterStore class: save(), load(), list_names()
    slugify.py               # slugify_name() function
models.py                    # (existing) Add character_library field to StoryInput
graph/
  nodes.py                   # (existing) Modify load_input_node to resolve character_library
config.py                    # (existing) Add character_library_dir setting
```

---

## Configuration

Add to `src/config.py` `Settings` class:

```python
character_library_dir: str = "character_library"
slack_bot_token: str = ""      # SLACK_BOT_TOKEN env var
slack_signing_secret: str = "" # SLACK_SIGNING_SECRET env var
slack_app_token: str = ""      # SLACK_APP_TOKEN env var (for socket mode)
```

---

## Key Interfaces

### CharacterStore

```python
class CharacterStore:
    def __init__(self, library_dir: Path): ...
    def save(self, profile: CharacterProfile) -> Path:
        """Save profile to YAML, return the file path."""
    def load(self, name: str) -> CharacterProfile:
        """Load by slugified name. Raises FileNotFoundError if missing."""
    def exists(self, name: str) -> bool:
        """Check if character exists."""
    def list_names(self) -> list[str]:
        """List all character names (slugified) in library."""
```

### WizardState

```python
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any

class WizardPhase(Enum):
    WAITING_NAME = auto()
    WAITING_DESCRIPTION = auto()
    WAITING_MOTIVATIONS = auto()
    WAITING_BACKSTORY = auto()
    WAITING_RELATIONSHIPS = auto()
    MODAL_1_OPEN = auto()
    MODAL_2_OPEN = auto()
    PREVIEW = auto()
    SAVED = auto()

@dataclass
class WizardState:
    phase: WizardPhase
    name: str = ""
    description: str = ""
    motivations: str = ""
    backstory: str = ""
    relationships: str = ""
    role: str = "supporting"
    agent_config_enabled: bool = False
    agent_type: str = "default"
    agent_properties: dict[str, Any] = field(default_factory=dict)
    agent_instructions: str = ""

    def to_character_profile(self) -> CharacterProfile:
        """Build CharacterProfile from collected state."""
```

### StateManager

```python
class StateManager:
    def __init__(self):
        self._states: dict[str, WizardState] = {}

    def get(self, user_id: str) -> WizardState | None: ...
    def set(self, user_id: str, state: WizardState) -> None: ...
    def clear(self, user_id: str) -> None: ...
    def start_new(self, user_id: str) -> WizardState:
        """Start new wizard, discarding any existing state."""
```

---

## Modal Specifications

### Modal 1: Role and Agent Config

**Block Kit Structure:**
```json
{
  "type": "modal",
  "callback_id": "modal_1_submit",
  "title": {"type": "plain_text", "text": "Character Setup"},
  "submit": {"type": "plain_text", "text": "Next"},
  "blocks": [
    {
      "type": "input",
      "block_id": "role_block",
      "element": {
        "type": "static_select",
        "action_id": "role_select",
        "options": [/* protagonist, antagonist, supporting, minor */]
      },
      "label": {"type": "plain_text", "text": "Role"}
    },
    {
      "type": "input",
      "block_id": "agent_toggle_block",
      "element": {
        "type": "checkboxes",
        "action_id": "agent_toggle",
        "options": [{"text": {"type": "plain_text", "text": "Enable agent configuration"}, "value": "enabled"}]
      },
      "label": {"type": "plain_text", "text": "Agent Configuration"},
      "optional": true
    },
    {
      "type": "input",
      "block_id": "agent_type_block",
      "element": {
        "type": "static_select",
        "action_id": "agent_type_select",
        "options": [/* dynamically from discover_character_agent_types() */]
      },
      "label": {"type": "plain_text", "text": "Agent Type"}
    }
  ]
}
```

**Note:** Block Kit does not support dynamically showing/hiding blocks within a single modal. The agent_type block is always rendered. On submission, if the toggle is off, the agent_type value is discarded. Validation only requires agent_type when the toggle is on.

### Modal 2: Agent Properties

**Dynamically generated based on `agent_type.property_schema`:**

For each property in schema:
- Create a number input block with label from property description
- Set placeholder showing range (0-100)
- Default value from schema default

Plus a multiline text input for `agent_instructions`.

### Correction Modal

**Combines all fields. All fields are always rendered (Block Kit limitation — no conditional visibility). Fields below the agent config checkbox are ignored on submission if the checkbox is unchecked:**
- Text inputs: name, description, motivations, backstory, relationships
- Static select: role
- Checkbox: agent config enabled
- Static select: agent type
- Number inputs: all properties for current agent type
- Multiline text: agent instructions

---

## PR/Commit Slices

### Slice 1: Character Store Foundation

**Description:** Create the `CharacterStore` module with save/load/list functionality and slugification, independent of both Slack and Storylord integration.

**Acceptance Criteria Addressed:** AC-5, AC-6, AC-7, AC-8

**Complexity:** S

**Dependencies:** None

**Files:**
- `src/character_store/__init__.py` (new)
- `src/character_store/store.py` (new)
- `src/character_store/slugify.py` (new)
- `tests/test_character_store.py` (new)
- `pyproject.toml` (add `python-slugify` dependency)

**Commits:**
1. Add `python-slugify` to dependencies
2. Implement `slugify_name()` with tests for edge cases
3. Implement `CharacterStore.save()` with YAML serialization
4. Implement `CharacterStore.load()` with Pydantic validation
5. Implement `CharacterStore.list_names()` and `exists()`

---

### Slice 2: Storylord Library Resolution

**Description:** Add `character_library` field to `StoryInput` and modify `load_input_node` to resolve and append library characters.

**Acceptance Criteria Addressed:** AC-1, AC-2, AC-3, AC-4

**Complexity:** S

**Dependencies:** Slice 1

**Files:**
- `src/models.py` (modify: add `character_library` field)
- `src/config.py` (modify: add `character_library_dir` setting)
- `src/graph/nodes.py` (modify: add library resolution logic)
- `tests/test_library_resolution.py` (new)

**Commits:**
1. Add `character_library: list[str] = Field(default_factory=list)` to `StoryInput`
2. Add `character_library_dir` to Settings with default
3. Implement library resolution in `load_input_node` with error handling
4. Add integration tests for library resolution scenarios

---

### Slice 3: Slack App Skeleton and State Management

**Description:** Set up the Bolt app structure, state management, and `/create-character` command that initiates the wizard.

**Acceptance Criteria Addressed:** AC-9, AC-28

**Complexity:** S

**Dependencies:** None (parallel with Slice 1-2)

**Files:**
- `src/slack_app/__init__.py` (new)
- `src/slack_app/app.py` (new)
- `src/slack_app/state.py` (new)
- `src/slack_app/handlers/__init__.py` (new)
- `src/slack_app/handlers/commands.py` (new)
- `src/config.py` (modify: add Slack settings)
- `pyproject.toml` (add `slack-bolt` dependency)
- `tests/test_wizard_state.py` (new)

**Commits:**
1. Add `slack-bolt` to dependencies and Slack settings to config
2. Implement `WizardState` dataclass and `WizardPhase` enum
3. Implement `StateManager` with get/set/clear/start_new
4. Create Bolt app skeleton with `/create-character` command handler
5. Add tests for state management

---

### Slice 4: Freeform Field Collection (DM Conversation)

**Description:** Implement the DM message handler that collects name, description, motivations, backstory, and relationships through conversation.

**Acceptance Criteria Addressed:** AC-10, AC-11, AC-12, AC-13, AC-29

**Complexity:** M

**Dependencies:** Slice 3

**Files:**
- `src/slack_app/handlers/messages.py` (new)
- `src/slack_app/app.py` (modify: register message handler)
- `tests/test_freeform_collection.py` (new)

**Commits:**
1. Implement message handler routing based on current phase
2. Implement `WAITING_NAME` handler with state transition
3. Implement handlers for description, motivations, backstory
4. Implement `WAITING_RELATIONSHIPS` handler with "skip" detection
5. Add invalid input handling with guidance messages
6. Add tests for conversation flow

---

### Slice 5: Modal 1 (Role and Agent Config Toggle)

**Description:** Implement Modal 1 with role selection and agent config toggle, plus its submission handler.

**Acceptance Criteria Addressed:** AC-14, AC-15, AC-16, AC-17

**Complexity:** M

**Dependencies:** Slice 4

**Files:**
- `src/slack_app/modals.py` (new)
- `src/slack_app/handlers/submissions.py` (new)
- `src/slack_app/app.py` (modify: register view submission handler)
- `tests/test_modal_1.py` (new)

**Commits:**
1. Implement `build_modal_1()` with static role options
2. Add dynamic agent type options from `discover_character_agent_types()`
3. Implement Modal 1 submission handler with toggle logic
4. Wire up modal opening after relationships collected
5. Add tests for modal structure and submission paths

---

### Slice 6: Modal 2 (Agent Properties)

**Description:** Implement Modal 2 with dynamic property inputs based on agent type schema.

**Acceptance Criteria Addressed:** AC-18, AC-19, AC-20, AC-21

**Complexity:** M

**Dependencies:** Slice 5

**Files:**
- `src/slack_app/modals.py` (modify: add `build_modal_2()`)
- `src/slack_app/handlers/submissions.py` (modify: add Modal 2 handler)
- `tests/test_modal_2.py` (new)

**Commits:**
1. Implement schema-to-blocks converter for property inputs
2. Implement `build_modal_2()` using agent type's `property_schema`
3. Implement Modal 2 submission handler with validation
4. Add range validation (0-100) with error messages
5. Add tests for both MBTI and default agent type modals

---

### Slice 7: Preview and Save

**Description:** Implement preview rendering, Save button handler, and integration with CharacterStore.

**Acceptance Criteria Addressed:** AC-22, AC-23, AC-26, AC-27

**Complexity:** S

**Dependencies:** Slice 1, Slice 6

**Files:**
- `src/slack_app/views.py` (new)
- `src/slack_app/handlers/actions.py` (new)
- `src/slack_app/app.py` (modify: register action handlers)
- `tests/test_preview_save.py` (new)

**Commits:**
1. Implement `build_preview_message()` with YAML code block
2. Implement `build_confirmation_message()` with file path
3. Implement Save button handler with CharacterStore integration
4. Wire up state clearing after save
5. Add tests for preview format and save flow

---

### Slice 8: Edit/Correction Modal

**Description:** Implement the correction modal that allows editing all fields, and wire up the Edit button.

**Acceptance Criteria Addressed:** AC-24, AC-25

**Complexity:** M

**Dependencies:** Slice 7

**Files:**
- `src/slack_app/modals.py` (modify: add `build_correction_modal()`)
- `src/slack_app/handlers/actions.py` (modify: add Edit handler)
- `src/slack_app/handlers/submissions.py` (modify: add correction modal handler)
- `tests/test_correction_modal.py` (new)

**Commits:**
1. Implement `build_correction_modal()` with all fields pre-populated
2. Implement Edit button handler to open correction modal
3. Implement correction modal submission handler
4. Wire up re-preview after correction submission
5. Add tests for edit flow and field preservation

---

## Synchronization Notes

### Must Stay in Sync

1. **Agent type property schemas and Modal 2 inputs**: Modal 2 dynamically reads `property_schema` from each `CharacterAgentType`. If a new agent type is added via entry points, Modal 2 will automatically support it. However, the modal builder must handle the JSON Schema format consistently.

2. **CharacterProfile model and YAML serialization**: Both `CharacterStore.save()` and the preview YAML block must serialize `CharacterProfile` identically. Use `profile.model_dump(mode='json', exclude_none=True)` for consistency.

3. **Role options in Modal 1 and Correction Modal**: The role dropdown options (protagonist, antagonist, supporting, minor) should be defined as a constant and shared between both modals.

4. **Slugification in CharacterStore and Storylord resolution**: Both use the same `slugify_name()` function to ensure filenames match lookup keys.

### Testing Considerations

- Unit tests should mock `discover_character_agent_types()` to provide predictable schemas
- Integration tests for Storylord should create temporary library directories
- Slack handler tests should use Bolt's test utilities or mock the Slack client
- End-to-end flow tests should verify the complete wizard cycle

---

## Entry Point for Slack App

Add to `pyproject.toml`:

```toml
[project.scripts]
storylord-slack = "slack_app:main"
```

Where `slack_app/__init__.py` exports:

```python
def main():
    from slack_app.app import create_app
    app = create_app()
    app.start(port=3000)  # or socket mode based on config
```

---

## Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| Missing character in library | Raise `FileNotFoundError` with character name and expected path |
| Invalid YAML in library file | Let Pydantic `ValidationError` propagate with field details |
| Slack API errors | Log error, send ephemeral "Something went wrong" to user |
| Modal validation failures | Return errors dict to Slack for inline display |
| State not found for user | Reply with guidance to run `/create-character` |

---

## Out of Scope (Explicit)

- OAuth / multi-workspace support
- Persistent state across bot restarts
- Character versioning or history
- Character deletion from Slack
- Character listing/browsing UI
- Real-time collaboration / locking
- Image upload for character portraits
