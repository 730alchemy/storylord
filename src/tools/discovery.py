"""Tool discovery via Python entry points.

This module provides functions to discover and load tool implementations
from installed packages that register entry points.
"""

from importlib.metadata import entry_points

from tools.protocols import Tool


def discover_tools() -> dict[str, type]:
    """Discover all registered tools from installed packages.

    Returns:
        A dictionary mapping tool names to their classes.
    """
    eps = entry_points(group="storylord.tools")
    return {ep.name: ep.load() for ep in eps}


def get_tool(name: str) -> Tool:
    """Get a tool instance by name.

    Args:
        name: The registered name of the tool.

    Returns:
        An instance of the requested tool.

    Raises:
        ValueError: If the tool name is not found.
    """
    tools = discover_tools()
    if name not in tools:
        available = ", ".join(sorted(tools.keys())) or "(none)"
        raise ValueError(f"Unknown tool '{name}'. Available: {available}")
    return tools[name]()


def list_tools() -> list[str]:
    """List all available tool names.

    Returns:
        A sorted list of registered tool names.
    """
    return sorted(discover_tools().keys())
