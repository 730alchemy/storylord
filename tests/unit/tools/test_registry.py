"""Unit tests for ToolRegistry class."""

from unittest.mock import MagicMock, patch

import pytest

from tools.registry import ToolRegistry
from tools.context import ToolExecutionContext


class TestToolRegistryInit:
    """Tests for ToolRegistry initialization."""

    @patch("tools.registry.discover_tools")
    def test_init_with_no_tools(self, mock_discover):
        """Empty registry when no tool names provided."""
        mock_discover.return_value = {}

        registry = ToolRegistry()

        assert len(registry) == 0

    @patch("tools.registry.discover_tools")
    def test_init_with_tool_names(self, mock_discover, mock_tool):
        """Registry loads specified tools from discovery."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])

        assert len(registry) == 1
        assert "mock_tool" in registry

    @patch("tools.registry.discover_tools")
    def test_init_with_multiple_tools(self, mock_discover):
        """Registry loads multiple tools."""
        tool1 = MagicMock()
        tool1.name = "tool1"
        tool2 = MagicMock()
        tool2.name = "tool2"

        mock_discover.return_value = {
            "tool1": lambda: tool1,
            "tool2": lambda: tool2,
        }

        registry = ToolRegistry(tool_names=["tool1", "tool2"])

        assert len(registry) == 2
        assert "tool1" in registry
        assert "tool2" in registry

    @patch("tools.registry.discover_tools")
    @patch("tools.registry.log")
    def test_init_logs_warning_for_unknown_tool(self, mock_log, mock_discover):
        """Warning is logged when tool not found."""
        mock_discover.return_value = {}

        ToolRegistry(tool_names=["nonexistent"])

        mock_log.warning.assert_called_with("tool_not_found", tool="nonexistent")

    @patch("tools.registry.discover_tools")
    def test_init_with_context_calls_configure(self, mock_discover, mock_tool):
        """Context is passed to tools during initialization."""
        mock_tool.configure = MagicMock()
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}
        context = ToolExecutionContext(run_id="test-123")

        ToolRegistry(tool_names=["mock_tool"], context=context)

        mock_tool.configure.assert_called_once_with(context)


class TestToolRegistryGet:
    """Tests for ToolRegistry.get() method."""

    @patch("tools.registry.discover_tools")
    def test_get_existing_tool(self, mock_discover, mock_tool):
        """Returns tool instance when it exists."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])
        result = registry.get("mock_tool")

        assert result is mock_tool

    @patch("tools.registry.discover_tools")
    def test_get_missing_tool_raises_keyerror(self, mock_discover):
        """Raises KeyError when tool not in registry."""
        mock_discover.return_value = {}
        registry = ToolRegistry()

        with pytest.raises(KeyError):
            registry.get("unknown")


class TestToolRegistryListTools:
    """Tests for ToolRegistry.list_tools() method."""

    @patch("tools.registry.discover_tools")
    def test_list_tools_empty_registry(self, mock_discover):
        """Empty registry returns empty list."""
        mock_discover.return_value = {}

        registry = ToolRegistry()
        result = registry.list_tools()

        assert result == []

    @patch("tools.registry.discover_tools")
    def test_list_tools_returns_schemas(self, mock_discover, mock_tool):
        """Returns properly formatted schema dictionaries."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])
        schemas = registry.list_tools()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "mock_tool"
        assert schemas[0]["description"] == "A mock tool for testing"
        assert "parameters" in schemas[0]

    @patch("tools.registry.discover_tools")
    def test_list_tools_schema_format(self, mock_discover):
        """Schema has required keys."""
        tool = MagicMock()
        tool.name = "test_tool"
        tool.description = "Test description"
        tool.get_schema.return_value = {
            "type": "object",
            "properties": {"x": {"type": "string"}},
        }
        mock_discover.return_value = {"test_tool": lambda: tool}

        registry = ToolRegistry(tool_names=["test_tool"])
        schemas = registry.list_tools()

        schema = schemas[0]
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema
        assert schema["parameters"]["type"] == "object"


class TestToolRegistryExecute:
    """Tests for ToolRegistry.execute() method."""

    @patch("tools.registry.discover_tools")
    def test_execute_calls_tool(self, mock_discover, mock_tool):
        """Execute calls the tool's execute method."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])
        result = registry.execute("mock_tool", param1="value1")

        mock_tool.execute.assert_called_once_with(param1="value1")
        assert result == {"result": "success"}

    @patch("tools.registry.discover_tools")
    def test_execute_missing_tool_raises_keyerror(self, mock_discover):
        """Raises KeyError when executing non-existent tool."""
        mock_discover.return_value = {}
        registry = ToolRegistry()

        with pytest.raises(KeyError):
            registry.execute("unknown")

    @patch("tools.registry.discover_tools")
    def test_execute_passes_multiple_params(self, mock_discover, mock_tool):
        """Execute passes all keyword arguments to tool."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])
        registry.execute("mock_tool", a=1, b=2, c="three")

        mock_tool.execute.assert_called_once_with(a=1, b=2, c="three")


class TestToolRegistryConfigure:
    """Tests for ToolRegistry.configure() method."""

    @patch("tools.registry.discover_tools")
    def test_configure_passes_context_to_tools(self, mock_discover):
        """Configure calls configure on each tool that supports it."""
        tool = MagicMock()
        tool.name = "configurable"
        tool.configure = MagicMock()
        mock_discover.return_value = {"configurable": lambda: tool}

        registry = ToolRegistry(tool_names=["configurable"])
        context = ToolExecutionContext(run_id="test-123")
        registry.configure(context)

        tool.configure.assert_called_with(context)

    @patch("tools.registry.discover_tools")
    def test_configure_skips_non_configurable_tools(self, mock_discover):
        """Configure doesn't fail on tools without configure method."""
        tool = MagicMock(spec=["name", "description", "get_schema", "execute"])
        tool.name = "simple"
        # Remove configure attribute
        del tool.configure
        mock_discover.return_value = {"simple": lambda: tool}

        registry = ToolRegistry(tool_names=["simple"])
        context = ToolExecutionContext(run_id="test-123")

        # Should not raise
        registry.configure(context)


class TestToolRegistryContains:
    """Tests for ToolRegistry.__contains__() method."""

    @patch("tools.registry.discover_tools")
    def test_contains_existing_tool(self, mock_discover, mock_tool):
        """Returns True for existing tool."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])

        assert "mock_tool" in registry

    @patch("tools.registry.discover_tools")
    def test_contains_missing_tool(self, mock_discover, mock_tool):
        """Returns False for missing tool."""
        mock_discover.return_value = {"mock_tool": lambda: mock_tool}

        registry = ToolRegistry(tool_names=["mock_tool"])

        assert "other_tool" not in registry


class TestToolRegistryLen:
    """Tests for ToolRegistry.__len__() method."""

    @patch("tools.registry.discover_tools")
    def test_len_empty_registry(self, mock_discover):
        """Empty registry has length 0."""
        mock_discover.return_value = {}

        registry = ToolRegistry()

        assert len(registry) == 0

    @patch("tools.registry.discover_tools")
    def test_len_with_tools(self, mock_discover):
        """Registry length equals number of tools."""
        tools = {f"tool{i}": lambda i=i: MagicMock(name=f"tool{i}") for i in range(5)}
        mock_discover.return_value = tools

        registry = ToolRegistry(tool_names=["tool0", "tool1", "tool2"])

        assert len(registry) == 3
