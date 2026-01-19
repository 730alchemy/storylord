"""Character list widget for selecting and managing characters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Select, Static, TextArea

if TYPE_CHECKING:
    from tui.character_studio import CharacterState


class NewCharacterModal:
    """Modal for creating a new character."""

    pass  # Implemented inline in CharacterListPane


class CharacterListPane(Vertical):
    """Pane for listing and selecting characters."""

    CSS = """
    CharacterListPane {
        height: 1fr;
        overflow-y: auto;
    }
    
    #character-table {
        height: 1fr;
        min-height: 5;
        width: 100%;
    }
    """

    class CharacterSelected(Message):
        """Message sent when a character is selected."""

        def __init__(self, name: str) -> None:
            self.name = name
            super().__init__()

    def __init__(self, state: "CharacterState") -> None:
        """Initialize the character list pane.

        Args:
            state: The shared character state.
        """
        super().__init__()
        self.state = state
        self._showing_new_form = False

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("Characters", classes="form-label")
        yield DataTable(id="character-table")
        with Horizontal(classes="button-row"):
            yield Button("New Character", id="btn-new", variant="primary")
            yield Button("Delete", id="btn-delete", variant="error")

        # New character form (hidden by default)
        with Vertical(id="new-character-form"):
            yield Static("New Character", classes="form-label")
            yield Static("Name:", classes="form-label")
            yield Input(id="new-name", placeholder="Character name")
            yield Static("Role:", classes="form-label")
            yield Select(
                [
                    ("Protagonist", "protagonist"),
                    ("Antagonist", "antagonist"),
                    ("Supporting", "supporting"),
                    ("Minor", "minor"),
                ],
                id="new-role",
                value="supporting",
            )
            yield Static("Description:", classes="form-label")
            yield TextArea(id="new-description")
            with Horizontal(classes="button-row"):
                yield Button("Create", id="btn-create", variant="success")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        """Initialize the table when mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Name", "Role", "Agent Type")
        table.cursor_type = "row"
        self._hide_new_form()
        self.refresh_list()

    def refresh_list(self) -> None:
        """Refresh the character list from state."""
        try:
            table = self.query_one("#character-table", DataTable)
        except Exception:
            # Fallback to any DataTable if ID query fails
            table = self.query_one(DataTable)

        # Ensure table is visible and displayed
        table.display = True
        table.visible = True

        # Ensure columns exist before adding rows
        if len(table.columns) == 0:
            table.add_columns("Name", "Role", "Agent Type")

        # Clear only rows, preserving columns
        table.clear(columns=False)

        for name, profile in self.state.profiles.items():
            agent_type = "default"
            if profile.agent_config:
                agent_type = profile.agent_config.agent_type
            table.add_row(name, profile.role, agent_type, key=name)

        # Force visual refresh and focus the table to ensure it renders
        table.refresh()
        if table.row_count > 0:
            # Focus the table to ensure it's visible and interactive
            table.focus()
            # Ensure table is still visible after operations
            table.display = True
            table.visible = True
            # Try to scroll to first row if method exists
            try:
                table.scroll_to_row(0)
            except AttributeError:
                # scroll_to_row may not be available in all Textual versions
                # Focusing the table should be sufficient
                pass

    def _show_new_form(self) -> None:
        """Show the new character form."""
        print("DEBUG: Showing new form")
        form = self.query_one("#new-character-form")
        form.display = True
        self._showing_new_form = True
        # Clear form
        self.query_one("#new-name", Input).value = ""
        self.query_one("#new-role", Select).value = "supporting"
        self.query_one("#new-description", TextArea).text = ""
        # Focus the name input
        self.query_one("#new-name", Input).focus()

    def _hide_new_form(self) -> None:
        """Hide the new character form."""
        print("DEBUG: Hiding new form")
        form = self.query_one("#new-character-form")
        form.display = False
        self._showing_new_form = False

    def action_new_character(self) -> None:
        """Show the new character form."""
        self._show_new_form()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        print(f"DEBUG: Button pressed: {event.button.id}")
        if event.button.id == "btn-new":
            self._show_new_form()
        elif event.button.id == "btn-cancel":
            self._hide_new_form()
        elif event.button.id == "btn-create":
            self._create_character()
        elif event.button.id == "btn-delete":
            self._delete_selected()

    def _create_character(self) -> None:
        """Create a new character from the form."""
        from models import CharacterProfile

        name = self.query_one("#new-name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        if name in self.state.profiles:
            self.notify(f"Character '{name}' already exists", severity="error")
            return

        role_value = self.query_one("#new-role", Select).value
        role = (
            str(role_value)
            if role_value is not Select.BLANK and role_value
            else "supporting"
        )
        description = self.query_one("#new-description", TextArea).text.strip()

        profile = CharacterProfile(
            name=name,
            description=description or "No description",
            role=role,
            motivations="",
            relationships="",
            backstory="",
        )

        self.state.add_character(profile)
        self.refresh_list()
        self._hide_new_form()
        self.notify(f"Created character: {name}")

        # Select the new character
        self.state.selected_character = name
        self.post_message(self.CharacterSelected(name))

    def _delete_selected(self) -> None:
        """Delete the selected character."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            row_key = table.get_row_key_at(table.cursor_row)
            if row_key:
                name = str(row_key.value)
                self.state.remove_character(name)
                self.refresh_list()
                self.notify(f"Deleted character: {name}")
                # Clear selection message
                self.post_message(self.CharacterSelected(""))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table."""
        if event.row_key:
            name = str(event.row_key.value)
            self.state.selected_character = name
            self.post_message(self.CharacterSelected(name))
