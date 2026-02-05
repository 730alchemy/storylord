# Spec Collaborator Memory

## Project: Storylord

AI-powered story generation framework with pluggable agents via Python entry points.

### Key Architecture Patterns

- **Entry point discovery**: Agents discovered via `importlib.metadata.entry_points()` in groups like `storylord.character_agents`
- **Property schemas**: Character agent types expose `property_schema` as JSON Schema dict (see `src/agents/character/protocols.py:67`)
- **Model validation**: YAML inputs validated immediately via Pydantic: `StoryInput.model_validate(yaml.safe_load(f))`
- **Graph-based pipeline**: Uses LangGraph with nodes in `src/graph/nodes.py`

### Existing Agent Types

| Type | Entry Point Group | Properties |
|------|-------------------|------------|
| `default` | `storylord.character_agents` | assertiveness, warmth, formality, verbosity, emotionality (0-100) |
| `mbti` | `storylord.character_agents` | extroversion, intuition, thinking, judging (0-100) |

### Key Files

- `src/models.py` - Pydantic models including `CharacterProfile`, `CharacterAgentConfig`, `StoryInput`
- `src/agents/discovery.py` - Agent discovery functions
- `src/graph/nodes.py` - Graph node implementations including `load_input_node`
- `src/config.py` - Settings via pydantic-settings

### Specification Conventions Used

- Acceptance criteria in Given/When/Then format
- PR slices sized for 1-3 day delivery
- Each slice maps to focused commits
- Interface definitions use Python type hints (not implementation)
- Explicit synchronization notes for things that must stay in sync

### Completed Specs

- `specs/slack-character-creator.md` - Slack bot for character creation with wizard flow
