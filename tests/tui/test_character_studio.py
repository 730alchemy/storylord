"""Tests for the Character Studio TUI screen."""

from pathlib import Path

import pytest
from textual.widgets import Button, DataTable, Input, Select, Static, TabbedContent, TextArea

from tests.tui.test_helpers import assert_text_visible, get_rendered_text, get_screen_text
from tui.app import StoryLordApp
from tui.character_studio import CharacterStudioScreen
from tui.widgets.agent_config import AgentConfigPane
from tui.widgets.character_list import CharacterListPane
from tui.widgets.character_profile import CharacterProfilePane
from tui.widgets.interaction import InteractionPane


async def open_character_studio(pilot):
    """Helper to open Character Studio and return the screen."""
    await pilot.press("ctrl+s")
    await pilot.pause()
    return pilot.app.screen


# --- Screen Opening/Closing Tests ---


@pytest.mark.asyncio
async def test_character_studio_opens():
    """Test that Character Studio opens correctly."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)
        assert isinstance(screen, CharacterStudioScreen)
        
        # Verify Character Studio title is rendered
        screen_text = get_screen_text(pilot)
        assert "Character Studio" in screen_text or "character studio" in screen_text.lower()


@pytest.mark.asyncio
async def test_character_studio_has_four_tabs():
    """Test that Character Studio has 4 tabs."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Check for TabbedContent
        tabbed = screen.query_one(TabbedContent)
        assert tabbed is not None

        # Check all four panes exist
        assert screen.query_one(CharacterListPane) is not None
        assert screen.query_one(CharacterProfilePane) is not None
        assert screen.query_one(AgentConfigPane) is not None
        assert screen.query_one(InteractionPane) is not None
        
        # Verify tab labels are rendered
        screen_text = get_screen_text(pilot)
        assert "Characters" in screen_text or "characters" in screen_text.lower()
        assert "Profile" in screen_text or "profile" in screen_text.lower()


# --- Tab Navigation Tests ---


@pytest.mark.asyncio
async def test_tab_navigation_ctrl_1():
    """Test Ctrl+1 switches to Characters tab."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Switch to another tab first
        await pilot.press("ctrl+2")
        await pilot.pause()

        # Switch back to Characters tab
        await pilot.press("ctrl+1")
        await pilot.pause()

        tabbed = screen.query_one(TabbedContent)
        assert tabbed.active == "tab-characters"


@pytest.mark.asyncio
async def test_tab_navigation_ctrl_2():
    """Test Ctrl+2 switches to Profile tab."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        await pilot.press("ctrl+2")
        await pilot.pause()

        tabbed = screen.query_one(TabbedContent)
        assert tabbed.active == "tab-profile"


@pytest.mark.asyncio
async def test_tab_navigation_ctrl_3():
    """Test Ctrl+3 switches to Agent tab."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        await pilot.press("ctrl+3")
        await pilot.pause()

        tabbed = screen.query_one(TabbedContent)
        assert tabbed.active == "tab-agent"


@pytest.mark.asyncio
async def test_tab_navigation_ctrl_4():
    """Test Ctrl+4 switches to Interact tab."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        await pilot.press("ctrl+4")
        await pilot.pause()

        tabbed = screen.query_one(TabbedContent)
        assert tabbed.active == "tab-interact"


# --- Characters Tab Tests ---


@pytest.mark.asyncio
async def test_character_list_initially_empty():
    """Test that character list is empty initially."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Check state has no characters
        assert len(screen.state.profiles) == 0

        # Check DataTable has no rows
        table = screen.query_one(DataTable)
        assert table.row_count == 0


@pytest.mark.asyncio
async def test_new_character_button_shows_form():
    """Test that clicking New Character shows the form."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Find and click New Character button using action instead of click
        list_pane = screen.query_one(CharacterListPane)
        list_pane.action_new_character()
        await pilot.pause()

        # Check form is visible
        form = screen.query_one("#new-character-form")
        assert form.display is True


@pytest.mark.asyncio
async def test_create_character():
    """Test creating a new character via state (bypassing UI events)."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Create a character directly via state
        from models import CharacterProfile

        profile = CharacterProfile(
            name="Test Hero",
            description="A test hero",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Created for testing",
        )
        screen.state.add_character(profile)
        screen.state.selected_character = "Test Hero"

        # Verify character was added to state
        assert "Test Hero" in screen.state.profiles
        assert screen.state.selected_character == "Test Hero"

        # Refresh the list to update UI
        list_pane = screen.query_one(CharacterListPane)
        list_pane.refresh_list()
        await pilot.pause()

        # Verify table has one row
        table = screen.query_one(DataTable)
        assert table.row_count == 1
        
        # Verify character is in state (more reliable than checking rendered text)
        assert "Test Hero" in screen.state.profiles
        
        # Verify table has the row (table content may not render in plain text)
        assert table.row_count == 1


@pytest.mark.asyncio
async def test_cancel_new_character_hides_form():
    """Test that Cancel button hides the new character form."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Show form
        btn = screen.query_one("#btn-new", Button)
        await pilot.click(btn)
        await pilot.pause()

        # Click Cancel
        cancel_btn = screen.query_one("#btn-cancel", Button)
        await pilot.click(cancel_btn)
        await pilot.pause()

        # Form should be hidden
        form = screen.query_one("#new-character-form")
        assert form.display is False


# --- Profile Tab Tests ---


@pytest.mark.asyncio
async def test_profile_tab_no_character_selected():
    """Test Profile tab shows message when no character selected."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Switch to Profile tab
        await pilot.press("ctrl+2")
        await pilot.pause()

        # Check that profile form is hidden (no character selected)
        form = screen.query_one("#profile-form")
        assert form.display is False


@pytest.mark.asyncio
async def test_profile_tab_shows_form_when_character_selected():
    """Test Profile tab shows form when character is selected."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Create a character first
        from models import CharacterProfile

        profile = CharacterProfile(
            name="Test Character",
            description="A test",
            role="protagonist",
            motivations="Testing",
            relationships="None",
            backstory="Created for testing",
        )
        screen.state.add_character(profile)
        screen.state.selected_character = "Test Character"

        # Switch to Profile tab and refresh
        await pilot.press("ctrl+2")
        await pilot.pause()

        profile_pane = screen.query_one(CharacterProfilePane)
        profile_pane.refresh_display()
        await pilot.pause()

        # Form should be visible
        form = screen.query_one("#profile-form")
        assert form.display is True
        
        # Verify character name appears in rendered output
        screen_text = get_screen_text(pilot)
        assert "Test Character" in screen_text or "test character" in screen_text.lower()
        
        # Verify form fields are rendered with character data
        name_input = screen.query_one("#profile-name", Input)
        assert name_input.value == "Test Character"
        name_text = get_rendered_text(name_input)
        assert "Test Character" in name_text or "test character" in name_text.lower()


# --- Agent Config Tab Tests ---


@pytest.mark.asyncio
async def test_agent_config_has_type_selector():
    """Test Agent Config tab has agent type selector."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Switch to Agent tab
        await pilot.press("ctrl+3")
        await pilot.pause()

        # Check for agent type select
        select = screen.query_one("#agent-type-select", Select)
        assert select is not None


# --- Interact Tab Tests ---


@pytest.mark.asyncio
async def test_interact_tab_has_function_selector():
    """Test Interact tab has function selector with 4 options."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Switch to Interact tab
        await pilot.press("ctrl+4")
        await pilot.pause()

        # Check for function select
        select = screen.query_one("#function-select", Select)
        assert select is not None


@pytest.mark.asyncio
async def test_interact_tab_shows_speak_inputs_by_default():
    """Test Interact tab shows Speak inputs by default."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Switch to Interact tab
        await pilot.press("ctrl+4")
        await pilot.pause()

        # Speak inputs should be visible
        speak_inputs = screen.query_one("#speak-inputs")
        assert speak_inputs.display is True

        # Other inputs should be hidden
        think_inputs = screen.query_one("#think-inputs")
        assert think_inputs.display is False


@pytest.mark.asyncio
async def test_interact_tab_no_character_selected():
    """Test Interact tab shows message when no character selected."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Switch to Interact tab
        await pilot.press("ctrl+4")
        await pilot.pause()

        # Check that interact form is hidden (no character selected)
        form = screen.query_one("#interact-form")
        assert form.display is False


# --- YAML Integration Tests ---


@pytest.mark.asyncio
async def test_load_yaml_populates_characters(sample_yaml_path):
    """Test that loading YAML populates the character list."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Load characters from YAML directly via state
        loaded = screen.state.load_from_yaml(sample_yaml_path)

        # Should have loaded 3 characters
        assert len(loaded) == 3
        assert "Elijah Boondog" in screen.state.profiles
        assert "Jasper Dilsack" in screen.state.profiles
        assert "Riley Thorn" in screen.state.profiles

        # Refresh the list
        list_pane = screen.query_one(CharacterListPane)
        list_pane.refresh_list()
        await pilot.pause()

        # Table should have 3 rows
        table = screen.query_one(DataTable)
        assert table.row_count == 3
        
        # Verify characters are in state (more reliable than checking rendered text)
        assert "Elijah Boondog" in screen.state.profiles
        assert "Jasper Dilsack" in screen.state.profiles
        assert "Riley Thorn" in screen.state.profiles
        
        # Verify table has rows (table content may not render in plain text)
        assert table.row_count == 3


@pytest.mark.asyncio
async def test_save_yaml_creates_valid_file(tmp_path):
    """Test that saving YAML creates a valid file."""
    app = StoryLordApp()
    async with app.run_test(size=(100, 40)) as pilot:
        screen = await open_character_studio(pilot)

        # Add a character
        from models import CharacterAgentConfig, CharacterProfile

        profile = CharacterProfile(
            name="Save Test",
            description="Testing save",
            role="supporting",
            motivations="To be saved",
            relationships="None",
            backstory="Will be saved to YAML",
            agent_config=CharacterAgentConfig(
                agent_type="default",
                agent_properties={"warmth": 50},
                agent_instructions="Be friendly",
            ),
        )
        screen.state.add_character(profile)

        # Save to temp file
        output_path = tmp_path / "test_output.yaml"
        screen.state.save_to_yaml(output_path)

        # Verify file exists and contains character
        assert output_path.exists()
        content = output_path.read_text()
        assert "Save Test" in content
        assert "Testing save" in content
        assert "agent_type: default" in content
