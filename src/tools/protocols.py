"""Protocol definitions for storylord tools.

These protocols define the contracts that all tool implementations must follow.
External packages can implement these protocols to create custom tools.
"""

from typing import Any, Protocol

from tools.context import ToolExecutionContext


class Tool(Protocol):
    """Protocol for tools that agents can use.

    Tools provide external capabilities to agents, such as web searches,
    database lookups, or API calls. Each tool must define its schema
    for LLM function calling and implement the execution logic.
    """

    name: str
    description: str

    def get_schema(self) -> dict:
        """Return JSON schema for tool parameters.

        The schema should follow the JSON Schema specification and describe
        the parameters that the tool accepts.

        Returns:
            A dictionary containing the JSON schema for the tool's parameters.
        """
        ...


class ContextAwareTool(Protocol):
    """Protocol for tools that accept runtime execution context."""

    def configure(self, context: ToolExecutionContext) -> None:
        """Provide runtime context to the tool before execution."""
        ...

    def execute(self, **params: Any) -> Any:
        """Execute the tool with the given parameters.

        Args:
            **params: The parameters for the tool, matching the schema.

        Returns:
            The result of the tool execution.
        """
        ...
