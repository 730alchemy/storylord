"""Character profile editing widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Select, Static, TextArea

if TYPE_CHECKING:
    from tui.character_studio import CharacterState


class CharacterProfilePane(Vertical):
    """Pane for viewing and editing character profile fields."""

    def __init__(self, state: "CharacterState") -> None:
        """Initialize the character profile pane.

        Args:
            state: The shared character state.
        """
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("No character selected", id="profile-status")

        with Vertical(id="profile-form"):
            yield Static("Name:", classes="form-label")
            yield Input(id="profile-name", placeholder="Character name")

            yield Static("Role:", classes="form-label")
            yield Select(
                [
                    ("Protagonist", "protagonist"),
                    ("Antagonist", "antagonist"),
                    ("Supporting", "supporting"),
                    ("Minor", "minor"),
                ],
                id="profile-role",
                value="supporting",
            )

            yield Static("Description:", classes="form-label")
            yield TextArea(id="profile-description")

            yield Static("Motivations:", classes="form-label")
            yield TextArea(id="profile-motivations")

            yield Static("Relationships:", classes="form-label")
            yield TextArea(id="profile-relationships")

            yield Static("Backstory:", classes="form-label")
            yield TextArea(id="profile-backstory")

            with Horizontal(classes="button-row"):
                yield Button("Save Profile", id="btn-save-profile", variant="primary")

    def on_mount(self) -> None:
        """Initialize the pane when mounted."""
        self._hide_form()
        self.refresh_display()

    def _hide_form(self) -> None:
        """Hide the profile form."""
        form = self.query_one("#profile-form")
        form.display = False

    def _show_form(self) -> None:
        """Show the profile form."""
        form = self.query_one("#profile-form")
        form.display = True

    def refresh_display(self) -> None:
        """Refresh the display from state."""
        profile = self.state.get_selected_profile()
        status = self.query_one("#profile-status", Static)

        if not profile:
            status.update("No character selected")
            self._hide_form()
            return

        status.update(f"Editing: {profile.name}")
        self._show_form()

        # Update form fields
        self.query_one("#profile-name", Input).value = profile.name
        self.query_one("#profile-role", Select).value = profile.role
        self.query_one("#profile-description", TextArea).text = profile.description
        self.query_one("#profile-motivations", TextArea).text = profile.motivations
        self.query_one("#profile-relationships", TextArea).text = profile.relationships
        self.query_one("#profile-backstory", TextArea).text = profile.backstory

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save-profile":
            self._save_profile()

    def _save_profile(self) -> None:
        """Save the current profile edits."""
        if not self.state.selected_character:
            self.notify("No character selected", severity="error")
            return

        from models import CharacterProfile

        old_name = self.state.selected_character
        new_name = self.query_one("#profile-name", Input).value.strip()

        if not new_name:
            self.notify("Name is required", severity="error")
            return

        # Check for name collision if name changed
        if new_name != old_name and new_name in self.state.profiles:
            self.notify(f"Character '{new_name}' already exists", severity="error")
            return

        role_value = self.query_one("#profile-role", Select).value
        role = (
            str(role_value)
            if role_value is not Select.BLANK and role_value
            else "supporting"
        )
        description = self.query_one("#profile-description", TextArea).text.strip()
        motivations = self.query_one("#profile-motivations", TextArea).text.strip()
        relationships = self.query_one("#profile-relationships", TextArea).text.strip()
        backstory = self.query_one("#profile-backstory", TextArea).text.strip()

        # Preserve agent config from existing profile
        old_profile = self.state.profiles.get(old_name)
        agent_config = old_profile.agent_config if old_profile else None

        profile = CharacterProfile(
            name=new_name,
            description=description or "No description",
            role=role,
            motivations=motivations,
            relationships=relationships,
            backstory=backstory,
            agent_config=agent_config,
        )

        self.state.update_profile(old_name, profile)
        self.notify(f"Saved profile: {new_name}")

        # Refresh the character list in the parent screen
        from tui.widgets.character_list import CharacterListPane

        try:
            list_pane = self.screen.query_one(CharacterListPane)
            list_pane.refresh_list()
        except Exception:
            pass  # List pane might not be mounted yet

        self.refresh_display()
