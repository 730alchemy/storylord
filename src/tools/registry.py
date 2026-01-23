"""Runtime tool registry for agents.

This module provides the ToolRegistry class that agents use to access
and execute tools during story generation.
"""

import structlog
from typing import Any

from tools.discovery import discover_tools
from tools.context import ToolExecutionContext
from tools.protocols import Tool

log = structlog.get_logger(__name__)


class ToolRegistry:
    """Runtime registry of tools available to an agent.

    The registry loads and instantiates tools by name, providing a unified
    interface for agents to discover tool schemas and execute tools.
    """

    def __init__(
        self,
        tool_names: list[str] | None = None,
        context: ToolExecutionContext | None = None,
    ):
        """Initialize the registry with the specified tools.

        Args:
            tool_names: List of tool names to load. If None, no tools are loaded.
            context: Optional runtime context to pass to tools.
        """
        self._tools: dict[str, Tool] = {}
        self._context = context

        if tool_names:
            available = discover_tools()
            for name in tool_names:
                if name in available:
                    self._tools[name] = available[name]()
                    log.debug("tool_loaded", tool=name)
                else:
                    log.warning("tool_not_found", tool=name)

        if self._context:
            self.configure(self._context)

    def configure(self, context: ToolExecutionContext) -> None:
        """Provide runtime context to tools that accept it."""
        self._context = context
        for tool in self._tools.values():
            configure = getattr(tool, "configure", None)
            if callable(configure):
                configure(context)

    def get(self, name: str) -> Tool:
        """Get a tool by name.

        Args:
            name: The name of the tool.

        Returns:
            The tool instance.

        Raises:
            KeyError: If the tool is not in the registry.
        """
        return self._tools[name]

    def list_tools(self) -> list[dict]:
        """Return tool schemas for LLM function calling.

        Returns:
            A list of tool schema dictionaries suitable for LLM binding.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_schema(),
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, **params: Any) -> Any:
        """Execute a tool by name.

        Args:
            name: The name of the tool to execute.
            **params: The parameters to pass to the tool.

        Returns:
            The result of the tool execution.

        Raises:
            KeyError: If the tool is not in the registry.
        """
        log.info(
            "tool_executing",
            tool=name,
            params=params,
            run_id=self._context.run_id if self._context else None,
            trace_id=self._context.trace_id if self._context else None,
            beat_reference=self._context.beat_reference if self._context else None,
        )
        result = self._tools[name].execute(**params)
        log.info(
            "tool_executed",
            tool=name,
            run_id=self._context.run_id if self._context else None,
            trace_id=self._context.trace_id if self._context else None,
            beat_reference=self._context.beat_reference if self._context else None,
        )
        return result

    def __len__(self) -> int:
        """Return the number of tools in the registry."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is in the registry."""
        return name in self._tools
