"""Character Studio screen for creating and interacting with characters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Static,
    TabbedContent,
    TabPane,
)

from agents.character.protocols import CharacterAgent
from agents.character.registry import CharacterRegistry
from agents.discovery import discover_character_agent_types
from models import CharacterAgentConfig, CharacterMemory, CharacterProfile
from tui.widgets.agent_config import AgentConfigPane
from tui.widgets.character_list import CharacterListPane
from tui.widgets.character_profile import CharacterProfilePane
from tui.widgets.interaction import InteractionPane


class CharacterState:
    """In-memory state for characters in the studio."""

    def __init__(self) -> None:
        """Initialize character state."""
        self.profiles: dict[str, CharacterProfile] = {}
        self.memories: dict[str, CharacterMemory] = {}
        self.registry: CharacterRegistry = CharacterRegistry(
            discover_character_agent_types()
        )
        self.selected_character: str | None = None
        self.unsaved_changes: bool = False
        self.conversation_history: list[str] = []

    def add_character(self, profile: CharacterProfile) -> None:
        """Add a character profile."""
        self.profiles[profile.name] = profile
        self.memories[profile.name] = CharacterMemory()
        self.unsaved_changes = True

    def remove_character(self, name: str) -> None:
        """Remove a character by name."""
        if name in self.profiles:
            del self.profiles[name]
        if name in self.memories:
            del self.memories[name]
        if self.selected_character == name:
            self.selected_character = None
        self.unsaved_changes = True

    def update_profile(self, name: str, profile: CharacterProfile) -> None:
        """Update a character profile."""
        old_name = name
        if old_name != profile.name:
            # Name changed, update keys
            if old_name in self.profiles:
                del self.profiles[old_name]
            if old_name in self.memories:
                self.memories[profile.name] = self.memories.pop(old_name)
            if self.selected_character == old_name:
                self.selected_character = profile.name
        self.profiles[profile.name] = profile
        self.unsaved_changes = True

    def get_selected_profile(self) -> CharacterProfile | None:
        """Get the currently selected character profile."""
        if self.selected_character:
            return self.profiles.get(self.selected_character)
        return None

    def get_selected_memory(self) -> CharacterMemory | None:
        """Get the currently selected character's memory."""
        if self.selected_character:
            return self.memories.get(self.selected_character)
        return None

    def get_or_create_agent(self, name: str) -> CharacterAgent | None:
        """Get or create an agent for the character."""
        if name not in self.profiles:
            return None

        profile = self.profiles[name]
        if self.registry.has_character(name):
            return self.registry.get_character(name)

        # Create new agent
        config = profile.agent_config or CharacterAgentConfig()
        agent_type = config.agent_type
        properties = config.agent_properties
        instructions = config.agent_instructions

        if agent_type not in self.registry.list_agent_types():
            # Fall back to default if type not available
            available = self.registry.list_agent_types()
            if available:
                agent_type = available[0]
            else:
                return None

        return self.registry.create_character(
            character_id=name,
            type_name=agent_type,
            profile=profile,
            properties=properties,
            instructions=instructions,
            memory=self.memories.get(name),
        )

    def load_from_yaml(self, path: Path) -> list[str]:
        """Load characters from a YAML file.

        Returns:
            List of loaded character names.
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        loaded = []
        characters = data.get("characters", [])
        for char_data in characters:
            # Parse agent config if present
            agent_config = None
            if "agent_config" in char_data:
                agent_config = CharacterAgentConfig(**char_data["agent_config"])
                del char_data["agent_config"]

            profile = CharacterProfile(**char_data, agent_config=agent_config)
            self.add_character(profile)
            loaded.append(profile.name)

        return loaded

    def save_to_yaml(self, path: Path) -> None:
        """Save characters to a YAML file."""
        characters: list[dict[str, Any]] = []
        for profile in self.profiles.values():
            char_data: dict[str, Any] = {
                "name": profile.name,
                "description": profile.description,
                "role": profile.role,
                "motivations": profile.motivations,
                "relationships": profile.relationships,
                "backstory": profile.backstory,
            }
            if profile.agent_config:
                char_data["agent_config"] = {
                    "agent_type": profile.agent_config.agent_type,
                    "agent_properties": profile.agent_config.agent_properties,
                    "agent_instructions": profile.agent_config.agent_instructions,
                }
            characters.append(char_data)

        data = {"characters": characters}
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        self.unsaved_changes = False


class CharacterStudioScreen(ModalScreen):
    """Main screen for the Character Studio."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("ctrl+n", "new_character", "New"),
        Binding("ctrl+w", "save_yaml", "Save YAML"),
        Binding("ctrl+l", "load_yaml", "Load"),
        Binding("ctrl+1", "tab_characters", "Characters"),
        Binding("ctrl+2", "tab_profile", "Profile"),
        Binding("ctrl+3", "tab_agent", "Agent"),
        Binding("ctrl+4", "tab_interact", "Interact"),
        Binding("ctrl+enter", "execute", "Execute"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    CSS = """
    CharacterStudioScreen {
        align: center middle;
    }

    CharacterStudioScreen > Vertical {
        width: 95%;
        height: 95%;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    #studio-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    TabbedContent {
        height: 1fr;
    }

    CharacterListPane, CharacterProfilePane, AgentConfigPane, InteractionPane {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }

    DataTable {
        height: 1fr;
    }

    .form-group {
        margin-bottom: 1;
    }

    .form-label {
        margin-bottom: 0;
    }

    TextArea {
        height: auto;
        min-height: 3;
        max-height: 10;
    }

    #chat-display {
        height: auto;
        min-height: 5;
        max-height: 20;
    }

    #response-display {
        height: auto;
        min-height: 5;
        max-height: 15;
    }

    #memory-display {
        height: auto;
        min-height: 3;
        max-height: 8;
    }

    #interact-form, #profile-form, #agent-form {
        height: auto;
    }

    #speak-inputs, #think-inputs, #choose-inputs, #answer-inputs {
        height: auto;
    }

    .button-row {
        height: auto;
        margin-top: 1;
    }

    Button {
        margin-right: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the Character Studio screen."""
        super().__init__()
        self.state = CharacterState()

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Vertical():
            yield Static("Character Studio", id="studio-title")
            with TabbedContent(id="studio-tabs"):
                with TabPane("Characters", id="tab-characters"):
                    yield CharacterListPane(self.state)
                with TabPane("Profile", id="tab-profile"):
                    yield CharacterProfilePane(self.state)
                with TabPane("Agent", id="tab-agent"):
                    yield AgentConfigPane(self.state)
                with TabPane("Interact", id="tab-interact"):
                    yield InteractionPane(self.state)
            yield Footer()

    def action_tab_characters(self) -> None:
        """Switch to Characters tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-characters"

    def action_tab_profile(self) -> None:
        """Switch to Profile tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-profile"

    def action_tab_agent(self) -> None:
        """Switch to Agent tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-agent"

    def action_tab_interact(self) -> None:
        """Switch to Interact tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-interact"

    def action_new_character(self) -> None:
        """Create a new character."""
        list_pane = self.query_one(CharacterListPane)
        list_pane.action_new_character()

    def action_save_yaml(self) -> None:
        """Save characters to YAML file."""
        from tui.app import FileInputModal

        self.app.push_screen(
            FileInputModal(placeholder="characters.yaml"), self._save_yaml_callback
        )

    def _save_yaml_callback(self, file_path: str | None) -> None:
        """Handle the save YAML callback."""
        if file_path:
            try:
                self.state.save_to_yaml(Path(file_path))
                self.notify(f"Saved to {file_path}")
            except Exception as e:
                self.notify(f"Error saving: {e}", severity="error")

    def action_load_yaml(self) -> None:
        """Load characters from YAML file."""
        from tui.app import FileInputModal

        self.app.push_screen(
            FileInputModal(placeholder="characters.yaml"), self._load_yaml_callback
        )

    def _load_yaml_callback(self, file_path: str | None) -> None:
        """Handle the load YAML callback."""
        if file_path:
            try:
                loaded = self.state.load_from_yaml(Path(file_path))
                self.notify(f"Loaded {len(loaded)} characters")
                
                # Switch to Characters tab FIRST to ensure table is visible
                tabs = self.query_one(TabbedContent)
                tabs.active = "tab-characters"
                
                # Use call_later to ensure tab switch completes before refreshing
                def refresh_after_tab_switch():
                    try:
                        list_pane = self.query_one(CharacterListPane)
                        if list_pane:
                            list_pane.refresh_list()
                            # Also ensure the table is visible
                            table = list_pane.query_one("#character-table", DataTable, default=None)
                            if table:
                                table.display = True
                                table.visible = True
                                table.refresh()
                    except Exception as e:
                        self.notify(f"Error refreshing list: {e}", severity="error")
                
                self.app.call_later(refresh_after_tab_switch)

                # Auto-select first character and refresh all panes
                if loaded:
                    self.state.selected_character = loaded[0]
                    self.query_one(CharacterProfilePane).refresh_display()
                    self.query_one(AgentConfigPane).refresh_display()
                    self.query_one(InteractionPane).refresh_display()
            except Exception as e:
                self.notify(f"Error loading: {e}", severity="error")

    def action_execute(self) -> None:
        """Execute the current interaction function."""
        interact_pane = self.query_one(InteractionPane)
        interact_pane.action_execute()

    def on_character_list_pane_character_selected(
        self, message: "CharacterListPane.CharacterSelected"
    ) -> None:
        """Handle character selection."""
        self.state.selected_character = message.name
        # Refresh other panes
        self.query_one(CharacterProfilePane).refresh_display()
        self.query_one(AgentConfigPane).refresh_display()
        self.query_one(InteractionPane).refresh_display()
