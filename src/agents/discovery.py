"""Agent discovery via Python entry points.

This module provides functions to discover and load agent implementations
from installed packages that register entry points.
"""

from importlib.metadata import entry_points

from agents.character.protocols import CharacterAgentType
from agents.protocols import Architect, Editor, Narrator


def discover_architects() -> dict[str, type]:
    """Discover all registered architects from installed packages.

    Returns:
        A dictionary mapping architect names to their classes.
    """
    eps = entry_points(group="storylord.architects")
    return {ep.name: ep.load() for ep in eps}


def discover_narrators() -> dict[str, type]:
    """Discover all registered narrators from installed packages.

    Returns:
        A dictionary mapping narrator names to their classes.
    """
    eps = entry_points(group="storylord.narrators")
    return {ep.name: ep.load() for ep in eps}


def get_architect(name: str) -> Architect:
    """Get an architect instance by name.

    Args:
        name: The registered name of the architect.

    Returns:
        An instance of the requested architect.

    Raises:
        ValueError: If the architect name is not found.
    """
    architects = discover_architects()
    if name not in architects:
        available = ", ".join(sorted(architects.keys())) or "(none)"
        raise ValueError(f"Unknown architect '{name}'. Available: {available}")
    return architects[name]()


def get_narrator(name: str) -> Narrator:
    """Get a narrator instance by name.

    Args:
        name: The registered name of the narrator.

    Returns:
        An instance of the requested narrator.

    Raises:
        ValueError: If the narrator name is not found.
    """
    narrators = discover_narrators()
    if name not in narrators:
        available = ", ".join(sorted(narrators.keys())) or "(none)"
        raise ValueError(f"Unknown narrator '{name}'. Available: {available}")
    return narrators[name]()


def list_architects() -> list[str]:
    """List all available architect names.

    Returns:
        A sorted list of registered architect names.
    """
    return sorted(discover_architects().keys())


def list_narrators() -> list[str]:
    """List all available narrator names.

    Returns:
        A sorted list of registered narrator names.
    """
    return sorted(discover_narrators().keys())


def discover_editors() -> dict[str, type]:
    """Discover all registered editors from installed packages.

    Returns:
        A dictionary mapping editor names to their classes.
    """
    eps = entry_points(group="storylord.editors")
    return {ep.name: ep.load() for ep in eps}


def get_editor(name: str) -> Editor:
    """Get an editor instance by name.

    Args:
        name: The registered name of the editor.

    Returns:
        An instance of the requested editor.

    Raises:
        ValueError: If the editor name is not found.
    """
    editors = discover_editors()
    if name not in editors:
        available = ", ".join(sorted(editors.keys())) or "(none)"
        raise ValueError(f"Unknown editor '{name}'. Available: {available}")
    return editors[name]()


def list_editors() -> list[str]:
    """List all available editor names.

    Returns:
        A sorted list of registered editor names.
    """
    return sorted(discover_editors().keys())


def discover_character_agent_types() -> dict[str, CharacterAgentType]:
    """Discover all registered character agent types from installed packages.

    Returns:
        A dictionary mapping character agent type names to their instances.
    """
    eps = entry_points(group="storylord.character_agents")
    return {ep.name: ep.load()() for ep in eps}


def get_character_agent_type(name: str) -> CharacterAgentType:
    """Get a character agent type instance by name.

    Args:
        name: The registered name of the character agent type.

    Returns:
        An instance of the requested character agent type.

    Raises:
        ValueError: If the character agent type name is not found.
    """
    types = discover_character_agent_types()
    if name not in types:
        available = ", ".join(sorted(types.keys())) or "(none)"
        raise ValueError(
            f"Unknown character agent type '{name}'. Available: {available}"
        )
    return types[name]


def list_character_agent_types() -> list[str]:
    """List all available character agent type names.

    Returns:
        A sorted list of registered character agent type names.
    """
    return sorted(discover_character_agent_types().keys())
