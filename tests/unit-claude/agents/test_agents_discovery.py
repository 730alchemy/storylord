"""Unit tests for agent discovery functions."""

from unittest.mock import MagicMock, patch

import pytest

from agents.discovery import (
    discover_architects,
    discover_narrators,
    discover_editors,
    discover_character_agent_types,
    get_architect,
    get_narrator,
    get_editor,
    get_character_agent_type,
    list_architects,
    list_narrators,
    list_editors,
    list_character_agent_types,
)


class TestDiscoverArchitects:
    """Tests for the discover_architects function."""

    @patch("agents.discovery.entry_points")
    def test_discover_architects_empty(self, mock_entry_points):
        """Returns empty dict when no architects registered."""
        mock_entry_points.return_value = []

        result = discover_architects()

        assert result == {}

    @patch("agents.discovery.entry_points")
    def test_discover_architects_loads_entry_points(self, mock_entry_points):
        """Loads architects from entry points."""
        mock_ep = MagicMock()
        mock_ep.name = "default"
        mock_ep.load.return_value = MagicMock

        mock_entry_points.return_value = [mock_ep]

        result = discover_architects()

        assert "default" in result
        mock_entry_points.assert_called_with(group="storylord.architects")


class TestGetArchitect:
    """Tests for the get_architect function."""

    @patch("agents.discovery.discover_architects")
    def test_get_architect_unknown_raises_valueerror(self, mock_discover):
        """Raises ValueError for unknown architect name."""
        mock_discover.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_architect("unknown")

        assert "Unknown architect 'unknown'" in str(exc_info.value)

    @patch("agents.discovery.discover_architects")
    def test_get_architect_error_message_lists_available(self, mock_discover):
        """Error message lists available architects."""
        mock_discover.return_value = {"default": MagicMock, "fancy": MagicMock}

        with pytest.raises(ValueError) as exc_info:
            get_architect("nonexistent")

        assert "Available: default, fancy" in str(exc_info.value)

    @patch("agents.discovery.discover_architects")
    def test_get_architect_returns_instance(self, mock_discover):
        """Returns an instance, not the class."""
        mock_instance = MagicMock()
        mock_class = MagicMock(return_value=mock_instance)
        mock_discover.return_value = {"default": mock_class}

        result = get_architect("default")

        assert result is mock_instance


class TestListArchitects:
    """Tests for the list_architects function."""

    @patch("agents.discovery.discover_architects")
    def test_list_architects_empty(self, mock_discover):
        """Returns empty list when no architects are registered."""
        mock_discover.return_value = {}

        result = list_architects()

        assert result == []

    @patch("agents.discovery.discover_architects")
    def test_list_architects_returns_sorted(self, mock_discover):
        """Returns sorted list of architect names."""
        mock_discover.return_value = {"zebra": MagicMock, "alpha": MagicMock}

        result = list_architects()

        assert result == ["alpha", "zebra"]


class TestDiscoverNarrators:
    """Tests for the discover_narrators function."""

    @patch("agents.discovery.entry_points")
    def test_discover_narrators_empty(self, mock_entry_points):
        """Returns empty dict when no narrators registered."""
        mock_entry_points.return_value = []

        result = discover_narrators()

        assert result == {}

    @patch("agents.discovery.entry_points")
    def test_discover_narrators_loads_entry_points(self, mock_entry_points):
        """Loads narrators from entry points."""
        mock_ep = MagicMock()
        mock_ep.name = "default"
        mock_ep.load.return_value = MagicMock

        mock_entry_points.return_value = [mock_ep]

        result = discover_narrators()

        assert "default" in result
        mock_entry_points.assert_called_with(group="storylord.narrators")


class TestGetNarrator:
    """Tests for the get_narrator function."""

    @patch("agents.discovery.discover_narrators")
    def test_get_narrator_unknown_raises_valueerror(self, mock_discover):
        """Raises ValueError for unknown narrator name."""
        mock_discover.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_narrator("unknown")

        assert "Unknown narrator 'unknown'" in str(exc_info.value)

    @patch("agents.discovery.discover_narrators")
    def test_get_narrator_error_message_lists_available(self, mock_discover):
        """Error message lists available narrators."""
        mock_discover.return_value = {"default": MagicMock}

        with pytest.raises(ValueError) as exc_info:
            get_narrator("nonexistent")

        assert "Available: default" in str(exc_info.value)

    @patch("agents.discovery.discover_narrators")
    def test_get_narrator_returns_instance(self, mock_discover):
        """Returns an instance, not the class."""
        mock_instance = MagicMock()
        mock_class = MagicMock(return_value=mock_instance)
        mock_discover.return_value = {"default": mock_class}

        result = get_narrator("default")

        assert result is mock_instance


class TestListNarrators:
    """Tests for the list_narrators function."""

    @patch("agents.discovery.discover_narrators")
    def test_list_narrators_empty(self, mock_discover):
        """Returns empty list when no narrators are registered."""
        mock_discover.return_value = {}

        result = list_narrators()

        assert result == []

    @patch("agents.discovery.discover_narrators")
    def test_list_narrators_returns_sorted(self, mock_discover):
        """Returns sorted list of narrator names."""
        mock_discover.return_value = {"zebra": MagicMock, "alpha": MagicMock}

        result = list_narrators()

        assert result == ["alpha", "zebra"]


class TestDiscoverEditors:
    """Tests for the discover_editors function."""

    @patch("agents.discovery.entry_points")
    def test_discover_editors_empty(self, mock_entry_points):
        """Returns empty dict when no editors registered."""
        mock_entry_points.return_value = []

        result = discover_editors()

        assert result == {}

    @patch("agents.discovery.entry_points")
    def test_discover_editors_loads_entry_points(self, mock_entry_points):
        """Loads editors from entry points."""
        mock_ep = MagicMock()
        mock_ep.name = "grammar"
        mock_ep.load.return_value = MagicMock

        mock_entry_points.return_value = [mock_ep]

        result = discover_editors()

        assert "grammar" in result
        mock_entry_points.assert_called_with(group="storylord.editors")


class TestGetEditor:
    """Tests for the get_editor function."""

    @patch("agents.discovery.discover_editors")
    def test_get_editor_unknown_raises_valueerror(self, mock_discover):
        """Raises ValueError for unknown editor name."""
        mock_discover.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_editor("unknown")

        assert "Unknown editor 'unknown'" in str(exc_info.value)

    @patch("agents.discovery.discover_editors")
    def test_get_editor_error_message_lists_available(self, mock_discover):
        """Error message lists available editors."""
        mock_discover.return_value = {"grammar": MagicMock, "style": MagicMock}

        with pytest.raises(ValueError) as exc_info:
            get_editor("nonexistent")

        assert "Available: grammar, style" in str(exc_info.value)

    @patch("agents.discovery.discover_editors")
    def test_get_editor_returns_instance(self, mock_discover):
        """Returns an instance, not the class."""
        mock_instance = MagicMock()
        mock_class = MagicMock(return_value=mock_instance)
        mock_discover.return_value = {"grammar": mock_class}

        result = get_editor("grammar")

        assert result is mock_instance


class TestListEditors:
    """Tests for the list_editors function."""

    @patch("agents.discovery.discover_editors")
    def test_list_editors_empty(self, mock_discover):
        """Returns empty list when no editors are registered."""
        mock_discover.return_value = {}

        result = list_editors()

        assert result == []

    @patch("agents.discovery.discover_editors")
    def test_list_editors_returns_sorted(self, mock_discover):
        """Returns sorted list of editor names."""
        mock_discover.return_value = {"zebra": MagicMock, "alpha": MagicMock}

        result = list_editors()

        assert result == ["alpha", "zebra"]


class TestDiscoverCharacterAgentTypes:
    """Tests for the discover_character_agent_types function."""

    @patch("agents.discovery.entry_points")
    def test_discover_character_agent_types_empty(self, mock_entry_points):
        """Returns empty dict when no character agent types registered."""
        mock_entry_points.return_value = []

        result = discover_character_agent_types()

        assert result == {}

    @patch("agents.discovery.entry_points")
    def test_discover_character_agent_types_loads_entry_points(self, mock_entry_points):
        """Loads character agent types from entry points."""
        mock_instance = MagicMock()
        mock_class = MagicMock(return_value=mock_instance)
        mock_ep = MagicMock()
        mock_ep.name = "default"
        mock_ep.load.return_value = mock_class

        mock_entry_points.return_value = [mock_ep]

        result = discover_character_agent_types()

        assert "default" in result
        # Note: character agent types are instantiated on discovery
        assert result["default"] is mock_instance
        mock_entry_points.assert_called_with(group="storylord.character_agents")


class TestGetCharacterAgentType:
    """Tests for the get_character_agent_type function."""

    @patch("agents.discovery.discover_character_agent_types")
    def test_get_character_agent_type_unknown_raises_valueerror(self, mock_discover):
        """Raises ValueError for unknown character agent type name."""
        mock_discover.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_character_agent_type("unknown")

        assert "Unknown character agent type 'unknown'" in str(exc_info.value)

    @patch("agents.discovery.discover_character_agent_types")
    def test_get_character_agent_type_error_message_lists_available(
        self, mock_discover
    ):
        """Error message lists available character agent types."""
        mock_discover.return_value = {"default": MagicMock(), "mbti": MagicMock()}

        with pytest.raises(ValueError) as exc_info:
            get_character_agent_type("nonexistent")

        assert "Available: default, mbti" in str(exc_info.value)

    @patch("agents.discovery.discover_character_agent_types")
    def test_get_character_agent_type_returns_instance(self, mock_discover):
        """Returns the instance directly (already instantiated)."""
        mock_instance = MagicMock()
        mock_discover.return_value = {"default": mock_instance}

        result = get_character_agent_type("default")

        assert result is mock_instance


class TestListCharacterAgentTypes:
    """Tests for the list_character_agent_types function."""

    @patch("agents.discovery.discover_character_agent_types")
    def test_list_character_agent_types_empty(self, mock_discover):
        """Returns empty list when no character agent types are registered."""
        mock_discover.return_value = {}

        result = list_character_agent_types()

        assert result == []

    @patch("agents.discovery.discover_character_agent_types")
    def test_list_character_agent_types_returns_sorted(self, mock_discover):
        """Returns sorted list of character agent type names."""
        mock_discover.return_value = {"zebra": MagicMock(), "alpha": MagicMock()}

        result = list_character_agent_types()

        assert result == ["alpha", "zebra"]
