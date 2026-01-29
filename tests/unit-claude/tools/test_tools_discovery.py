"""Unit tests for tool discovery functions."""

from unittest.mock import MagicMock, patch

import pytest

from tools.discovery import discover_tools, get_tool, list_tools


class TestDiscoverTools:
    """Tests for the discover_tools function."""

    @patch("tools.discovery.entry_points")
    def test_discover_tools_empty(self, mock_entry_points):
        """Returns empty dict when no tools registered."""
        mock_entry_points.return_value = []

        result = discover_tools()

        assert result == {}

    @patch("tools.discovery.entry_points")
    def test_discover_tools_loads_entry_points(self, mock_entry_points):
        """Loads tools from entry points."""
        mock_ep1 = MagicMock()
        mock_ep1.name = "tool1"
        mock_ep1.load.return_value = MagicMock

        mock_ep2 = MagicMock()
        mock_ep2.name = "tool2"
        mock_ep2.load.return_value = MagicMock

        mock_entry_points.return_value = [mock_ep1, mock_ep2]

        result = discover_tools()

        assert "tool1" in result
        assert "tool2" in result
        mock_entry_points.assert_called_with(group="storylord.tools")


class TestGetTool:
    """Tests for the get_tool function."""

    @patch("tools.discovery.discover_tools")
    def test_get_tool_unknown_raises_valueerror(self, mock_discover):
        """Raises ValueError for unknown tool name."""
        mock_discover.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_tool("unknown")

        assert "Unknown tool 'unknown'" in str(exc_info.value)

    @patch("tools.discovery.discover_tools")
    def test_get_tool_error_message_lists_available(self, mock_discover):
        """Error message lists available tools."""
        mock_tool = MagicMock
        mock_discover.return_value = {"tool_a": mock_tool, "tool_b": mock_tool}

        with pytest.raises(ValueError) as exc_info:
            get_tool("nonexistent")

        assert "Available: tool_a, tool_b" in str(exc_info.value)

    @patch("tools.discovery.discover_tools")
    def test_get_tool_error_message_when_none_available(self, mock_discover):
        """Error message shows (none) when no tools available."""
        mock_discover.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_tool("any")

        assert "Available: (none)" in str(exc_info.value)

    @patch("tools.discovery.discover_tools")
    def test_get_tool_returns_instance(self, mock_discover):
        """Returns an instance, not the class."""
        mock_instance = MagicMock()
        mock_class = MagicMock(return_value=mock_instance)
        mock_discover.return_value = {"my_tool": mock_class}

        result = get_tool("my_tool")

        assert result is mock_instance
        mock_class.assert_called_once()


class TestListTools:
    """Tests for the list_tools function."""

    @patch("tools.discovery.discover_tools")
    def test_list_tools_empty(self, mock_discover):
        """Returns empty list when no tools registered."""
        mock_discover.return_value = {}

        result = list_tools()

        assert result == []

    @patch("tools.discovery.discover_tools")
    def test_list_tools_returns_sorted(self, mock_discover):
        """Returns sorted list of tool names."""
        mock_discover.return_value = {
            "zebra": MagicMock,
            "alpha": MagicMock,
            "beta": MagicMock,
        }

        result = list_tools()

        assert result == ["alpha", "beta", "zebra"]
