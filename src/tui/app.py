"""StoryLord TUI application."""

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Select, Static, TextArea
from textual.worker import get_current_worker

from agents.discovery import (
    get_editor,
    list_architects,
    list_character_agent_types,
    list_editors,
    list_narrators,
)
from models import EditorInput


class EditorScreen(ModalScreen):
    """Screen for running the editor agent."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("ctrl+r", "run_editor", "Run"),
        Binding("ctrl+o", "load_file", "Open"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        editors = list_editors()
        with Vertical():
            yield Static("Editor - Enter text to improve", id="editor-title")
            yield Select(
                [(name, name) for name in editors],
                id="editor-select",
                value=editors[0] if editors else None,
                prompt="Select editor",
            )
            yield Static("Input:", id="input-label")
            yield TextArea(id="editor-input")
            yield Static("Edited Text:", id="output-label")
            yield TextArea(id="editor-output", read_only=True)
            yield Footer()

    def action_run_editor(self) -> None:
        """Run the editor agent on the input text."""
        input_area = self.query_one("#editor-input", TextArea)
        output_area = self.query_one("#editor-output", TextArea)
        select = self.query_one("#editor-select", Select)

        text = input_area.text
        if not text.strip():
            output_area.clear()
            output_area.text = "No input text provided."
            return

        if select.value is None:
            output_area.clear()
            output_area.text = "No editor selected."
            return

        output_area.clear()
        output_area.text = "Running editor..."
        self._run_editor_worker(text, select.value)

    @work(thread=True)
    def _run_editor_worker(self, text: str, editor_name: str) -> None:
        """Run the editor in a background thread."""
        worker = get_current_worker()
        editor = get_editor(editor_name)
        result = editor.edit(EditorInput(text=text))
        if not worker.is_cancelled:
            self.app.call_from_thread(self._update_output, result.text)

    def _update_output(self, text: str) -> None:
        """Update the output area with the result."""
        output_area = self.query_one("#editor-output", TextArea)
        output_area.clear()
        output_area.text = text

    def on_select_changed(self, event: Select.Changed) -> None:
        """Clear output when editor selection changes."""
        output_area = self.query_one("#editor-output", TextArea)
        output_area.clear()

    def action_load_file(self) -> None:
        """Prompt for a file path and load its contents."""
        self.app.push_screen(FileInputModal(), self._load_file_callback)

    def _load_file_callback(self, file_path: str | None) -> None:
        """Load the file contents into the input area."""
        if file_path:
            try:
                with open(file_path) as f:
                    content = f.read()
                input_area = self.query_one("#editor-input", TextArea)
                input_area.text = content
            except FileNotFoundError:
                output_area = self.query_one("#editor-output", TextArea)
                output_area.text = f"File not found: {file_path}"
            except Exception as e:
                output_area = self.query_one("#editor-output", TextArea)
                output_area.text = f"Error loading file: {e}"


class FileInputModal(ModalScreen[str | None]):
    """Modal for entering a file path."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def __init__(self, placeholder: str = "/path/to/file.txt") -> None:
        """Initialize the file input modal.

        Args:
            placeholder: Placeholder text for the input field.
        """
        super().__init__()
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical():
                yield Static("Enter file path:")
                yield Input(id="file-path-input", placeholder=self._placeholder)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in the input."""
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        """Cancel and return None."""
        self.dismiss(None)


class AgentsModal(ModalScreen):
    """Modal screen displaying available agents."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        architects = list_architects()
        narrators = list_narrators()
        editors = list_editors()
        character_agents = list_character_agent_types()

        content = ["Available Agents", ""]
        content.append("Architects:")
        content.extend(f"  - {name}" for name in architects)
        content.append("")
        content.append("Narrators:")
        content.extend(f"  - {name}" for name in narrators)
        content.append("")
        content.append("Editors:")
        content.extend(f"  - {name}" for name in editors)
        content.append("")
        content.append("Character Agents:")
        content.extend(f"  - {name}" for name in character_agents)
        content.append("")
        content.append("Press ESC to close")

        with Center():
            with Vertical():
                yield Static("\n".join(content))


class StoryLordApp(App):
    """Main TUI application for StoryLord."""

    BINDINGS = [
        Binding("ctrl+a", "show_agents", "Agents"),
        Binding("ctrl+e", "show_editor", "Editor"),
        Binding("ctrl+s", "show_character_studio", "Characters"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Welcome to storyland")
        yield Footer()

    def action_show_agents(self) -> None:
        """Show the agents modal."""
        self.push_screen(AgentsModal())

    def action_show_editor(self) -> None:
        """Show the editor screen."""
        self.push_screen(EditorScreen())

    def action_show_character_studio(self) -> None:
        """Show the character studio screen."""
        from tui.character_studio import CharacterStudioScreen

        self.push_screen(CharacterStudioScreen())
