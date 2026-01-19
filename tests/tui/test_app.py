"""Tests for the main StoryLord TUI application."""

import pytest

from tui.app import AgentsModal, EditorScreen, StoryLordApp
from tui.character_studio import CharacterStudioScreen


@pytest.mark.asyncio
async def test_app_launches():
    """Test that the app launches without error."""
    app = StoryLordApp()
    async with app.run_test(size=(80, 24)) as pilot:
        # App should be running
        assert pilot.app is not None
        assert pilot.app.is_running


@pytest.mark.asyncio
async def test_ctrl_a_opens_agents_modal():
    """Test that Ctrl+A opens the AgentsModal."""
    app = StoryLordApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("ctrl+a")
        await pilot.pause()

        # Check that AgentsModal is now the active screen
        assert isinstance(pilot.app.screen, AgentsModal)


@pytest.mark.asyncio
async def test_ctrl_e_opens_editor_screen():
    """Test that Ctrl+E opens the EditorScreen."""
    app = StoryLordApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("ctrl+e")
        await pilot.pause()

        # Check that EditorScreen is now the active screen
        assert isinstance(pilot.app.screen, EditorScreen)


@pytest.mark.asyncio
async def test_ctrl_s_opens_character_studio():
    """Test that Ctrl+S opens the CharacterStudioScreen."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.press("ctrl+s")
        await pilot.pause()

        # Check that CharacterStudioScreen is now the active screen
        assert isinstance(pilot.app.screen, CharacterStudioScreen)


@pytest.mark.asyncio
async def test_escape_closes_modal():
    """Test that Escape closes modal screens."""
    app = StoryLordApp()
    async with app.run_test(size=(80, 24)) as pilot:
        # Open agents modal
        await pilot.press("ctrl+a")
        await pilot.pause()
        assert isinstance(pilot.app.screen, AgentsModal)

        # Press escape to close
        await pilot.press("escape")
        await pilot.pause()

        # Should be back to main screen (not AgentsModal)
        assert not isinstance(pilot.app.screen, AgentsModal)


@pytest.mark.asyncio
async def test_escape_closes_character_studio():
    """Test that Escape closes the Character Studio."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        # Open character studio
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert isinstance(pilot.app.screen, CharacterStudioScreen)

        # Press escape to close
        await pilot.press("escape")
        await pilot.pause()

        # Should be back to main screen
        assert not isinstance(pilot.app.screen, CharacterStudioScreen)
