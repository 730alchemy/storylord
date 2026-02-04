# AGENTS.md

## Project overview
Storylord is an AI-powered story generation framework with pluggable agents (architect, narrator, editor, character agents, tools).

## Environment
- Python == 3.13
- Dependency manager: PDM

## Common commands
- Install deps: `pdm install`
- Run app: `pdm start` (or `pdm run python src/story_lord.py`)
- Format/lint (required): `pdm fmt`
- Lint check only: `pdm lint`
- Tests: `pdm test`

## Coding conventions
- Use `pdm run python` when running Python scripts that rely on project dependencies.
- Keep new agents under `src/agents/` and follow the existing module layout.
- If you add a new agent type or tool, register it in `pyproject.toml` under `project.entry-points`.

## Repository layout
- `src/agents/`: agent implementations (architect, narrator, editor, character agents)
- `src/tools/`: tool implementations
- `src/graph/`: graph orchestration
- `src/tui/`: textual UI
- `tests/`: pytest suite
