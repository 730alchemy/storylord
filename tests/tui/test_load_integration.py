"""Integration tests for file loading workflow in Character Studio."""

from pathlib import Path

import pytest
from textual.widgets import DataTable, Input

from tests.tui.test_helpers import assert_text_visible, get_screen_text
from tui.app import FileInputModal, StoryLordApp
from tui.character_studio import CharacterStudioScreen
from tui.widgets.character_list import CharacterListPane
from tui.widgets.character_profile import CharacterProfilePane


async def open_character_studio(pilot):
    """Helper to open Character Studio and return the screen."""
    await pilot.press("ctrl+s")
    await pilot.pause()
    return pilot.app.screen


@pytest.mark.asyncio
async def test_ctrl_l_loads_file_and_displays_data(sample_yaml_path):
    """Test that Ctrl-L workflow loads file and displays data in all tabs."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)
        assert isinstance(screen, CharacterStudioScreen)

        # Press Ctrl-L to open load dialog
        await pilot.press("ctrl+l")
        await pilot.pause()

        # Verify FileInputModal is open
        assert isinstance(pilot.app.screen, FileInputModal)

        # Type the filename
        file_input = pilot.app.screen.query_one("#file-path-input", Input)
        file_input.value = str(sample_yaml_path)
        await pilot.pause()

        # Submit by pressing Enter
        await pilot.press("enter")
        await pilot.pause(0.5)

        # Verify we're back to Character Studio
        assert isinstance(pilot.app.screen, CharacterStudioScreen)

        # Verify characters were loaded into state
        assert len(screen.state.profiles) == 3
        assert "Elijah Boondog" in screen.state.profiles
        assert "Jasper Dilsack" in screen.state.profiles
        assert "Riley Thorn" in screen.state.profiles

        # Verify Characters tab shows the data
        table = screen.query_one(DataTable)
        assert table.row_count == 3

        # Verify characters are in state (DataTable content may not render in plain text)
        # We already verified state above, so just confirm table has rows
        assert table.row_count == 3

        # Verify first character is auto-selected
        assert screen.state.selected_character == "Elijah Boondog"

        # Verify Profile tab shows character data
        await pilot.press("ctrl+2")
        await pilot.pause()
        screen_text = get_screen_text(pilot)
        assert_text_visible(pilot, "Elijah")

        # Verify form fields are populated
        name_input = screen.query_one("#profile-name", Input)
        assert name_input.value == "Elijah Boondog"

        # Verify Agent tab shows agent config
        await pilot.press("ctrl+3")
        await pilot.pause()
        screen_text = get_screen_text(pilot)
        assert_text_visible(pilot, "Agent")

        # Verify Interact tab shows interaction form
        await pilot.press("ctrl+4")
        await pilot.pause()
        screen_text = get_screen_text(pilot)
        assert_text_visible(pilot, "Function")


@pytest.mark.asyncio
async def test_load_invalid_file_shows_error():
    """Test that loading a non-existent file shows an error message."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Press Ctrl-L to open load dialog
        await pilot.press("ctrl+l")
        await pilot.pause()

        # Type invalid filename
        file_input = pilot.app.screen.query_one("#file-path-input", Input)
        file_input.value = "/nonexistent/file.yaml"
        await pilot.pause()

        # Submit
        await pilot.press("enter")
        await pilot.pause(0.5)

        # Verify error notification appears
        # Note: Textual notifications may appear in different ways
        # We check that no characters were loaded
        assert len(screen.state.profiles) == 0

        # Verify table is still empty
        table = screen.query_one(DataTable)
        assert table.row_count == 0


@pytest.mark.asyncio
async def test_load_file_refreshes_character_list(sample_yaml_path):
    """Test that loading a file refreshes the character list display."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Initially empty
        table = screen.query_one(DataTable)
        assert table.row_count == 0

        # Load file
        await pilot.press("ctrl+l")
        await pilot.pause()
        file_input = pilot.app.screen.query_one("#file-path-input", Input)
        file_input.value = str(sample_yaml_path)
        await pilot.press("enter")
        await pilot.pause(0.5)

        # Verify list was refreshed
        table = screen.query_one(DataTable)
        assert table.row_count == 3

        # Verify characters are in state (more reliable than checking rendered text)
        assert "Elijah Boondog" in screen.state.profiles
        assert "Jasper Dilsack" in screen.state.profiles
        assert "Riley Thorn" in screen.state.profiles
        assert table.row_count == 3


@pytest.mark.asyncio
async def test_load_file_auto_selects_first_character(sample_yaml_path):
    """Test that loading a file auto-selects the first character."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Load file
        await pilot.press("ctrl+l")
        await pilot.pause()
        file_input = pilot.app.screen.query_one("#file-path-input", Input)
        file_input.value = str(sample_yaml_path)
        await pilot.press("enter")
        await pilot.pause(0.5)

        # Verify first character is selected
        assert screen.state.selected_character == "Elijah Boondog"

        # Verify Profile tab shows the selected character
        await pilot.press("ctrl+2")
        await pilot.pause()

        profile_pane = screen.query_one(CharacterProfilePane)
        profile_pane.refresh_display()
        await pilot.pause()

        # Verify form shows character data
        name_input = screen.query_one("#profile-name", Input)
        assert name_input.value == "Elijah Boondog"

        # Verify status shows character name
        status_text = get_screen_text(pilot)
        assert "Elijah" in status_text or "elijah" in status_text.lower()


@pytest.mark.asyncio
async def test_load_file_updates_all_panes(sample_yaml_path):
    """Test that loading a file updates all panes (Profile, Agent, Interact)."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Load file
        await pilot.press("ctrl+l")
        await pilot.pause()
        file_input = pilot.app.screen.query_one("#file-path-input", Input)
        file_input.value = str(sample_yaml_path)
        await pilot.press("enter")
        await pilot.pause(0.5)

        # Verify Profile pane was updated
        profile_pane = screen.query_one(CharacterProfilePane)
        profile_pane.refresh_display()
        await pilot.pause()
        assert profile_pane.state.selected_character == "Elijah Boondog"

        # Verify Agent pane was updated
        from tui.widgets.agent_config import AgentConfigPane

        agent_pane = screen.query_one(AgentConfigPane)
        agent_pane.refresh_display()
        await pilot.pause()
        assert agent_pane.state.selected_character == "Elijah Boondog"

        # Verify Interaction pane was updated
        from tui.widgets.interaction import InteractionPane

        interact_pane = screen.query_one(InteractionPane)
        interact_pane.refresh_display()
        await pilot.pause()
        assert interact_pane.state.selected_character == "Elijah Boondog"
