"""Interaction widget for dialogue with characters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Select, Static, TextArea
from textual.worker import get_current_worker

from agents.character.protocols import (
    AnswerInput,
    CharacterResponse,
    ChooseInput,
    SpeakInput,
    ThinkInput,
)

if TYPE_CHECKING:
    from tui.character_studio import CharacterState


class InteractionPane(Vertical):
    """Pane for interacting with characters via speak, think, choose, answer."""

    FUNCTION_SPEAK = "speak"
    FUNCTION_THINK = "think"
    FUNCTION_CHOOSE = "choose"
    FUNCTION_ANSWER = "answer"

    def __init__(self, state: "CharacterState") -> None:
        """Initialize the interaction pane.

        Args:
            state: The shared character state.
        """
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("No character selected", id="interact-status")

        with Vertical(id="interact-form"):
            # Character info header
            with Horizontal(id="character-info"):
                yield Static("Character: ", classes="form-label")
                yield Static("-", id="current-character-name")
                yield Static(" | Emotional State: ", classes="form-label")
                yield Static("neutral", id="emotional-state")

            # Function selector
            yield Static("Function:", classes="form-label")
            yield Select(
                [
                    ("Speak (dialogue)", self.FUNCTION_SPEAK),
                    ("Think (internal)", self.FUNCTION_THINK),
                    ("Choose (decision)", self.FUNCTION_CHOOSE),
                    ("Answer (respond)", self.FUNCTION_ANSWER),
                ],
                id="function-select",
                value=self.FUNCTION_SPEAK,
            )

            # Chat display (for speak conversations)
            yield Static("Conversation:", classes="form-label")
            yield TextArea(id="chat-display", read_only=True)

            # Speak inputs
            with Vertical(id="speak-inputs"):
                yield Static("Scene Context:", classes="form-label")
                yield TextArea(id="speak-scene-context")
                yield Static("Your message:", classes="form-label")
                yield Input(id="speak-prompt", placeholder="What do you say?")

            # Think inputs
            with Vertical(id="think-inputs"):
                yield Static("Scene Context:", classes="form-label")
                yield TextArea(id="think-scene-context")
                yield Static("Situation:", classes="form-label")
                yield TextArea(id="think-situation")

            # Choose inputs
            with Vertical(id="choose-inputs"):
                yield Static("Scene Context:", classes="form-label")
                yield TextArea(id="choose-scene-context")
                yield Static("Choices (one per line):", classes="form-label")
                yield TextArea(id="choose-choices")
                yield Static("Additional Context:", classes="form-label")
                yield TextArea(id="choose-context")

            # Answer inputs
            with Vertical(id="answer-inputs"):
                yield Static("Question:", classes="form-label")
                yield Input(id="answer-question", placeholder="What is the question?")
                yield Static("Asking Agent:", classes="form-label")
                yield Input(id="answer-asking-agent", placeholder="Who is asking?")
                yield Static("Context:", classes="form-label")
                yield TextArea(id="answer-context")

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Execute", id="btn-execute", variant="primary")
                yield Button("Clear Conversation", id="btn-clear")

            # Response display (for non-speak functions)
            yield Static("Response:", classes="form-label")
            yield TextArea(id="response-display", read_only=True)

            # Memory summary
            yield Static("Memory Summary:", classes="form-label")
            yield TextArea(id="memory-display", read_only=True)

    def on_mount(self) -> None:
        """Initialize the pane when mounted."""
        self._hide_form()
        self._setup_input_fields()
        self.refresh_display()

    def _hide_form(self) -> None:
        """Hide the interaction form."""
        form = self.query_one("#interact-form")
        form.display = False

    def _show_form(self) -> None:
        """Show the interaction form."""
        form = self.query_one("#interact-form")
        form.display = True

    def _setup_input_fields(self) -> None:
        """Show/hide input fields based on the selected function."""
        select = self.query_one("#function-select", Select)
        function = select.value

        # Hide all input containers
        self.query_one("#speak-inputs").display = False
        self.query_one("#think-inputs").display = False
        self.query_one("#choose-inputs").display = False
        self.query_one("#answer-inputs").display = False

        # Show the appropriate container
        if function == self.FUNCTION_SPEAK:
            self.query_one("#speak-inputs").display = True
        elif function == self.FUNCTION_THINK:
            self.query_one("#think-inputs").display = True
        elif function == self.FUNCTION_CHOOSE:
            self.query_one("#choose-inputs").display = True
        elif function == self.FUNCTION_ANSWER:
            self.query_one("#answer-inputs").display = True

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle function selection change."""
        if event.select.id == "function-select":
            self._setup_input_fields()

    def refresh_display(self) -> None:
        """Refresh the display from state."""
        profile = self.state.get_selected_profile()
        status = self.query_one("#interact-status", Static)

        if not profile:
            status.update("No character selected")
            self._hide_form()
            return

        status.update(f"Interacting with: {profile.name}")
        self._show_form()

        # Update character info
        self.query_one("#current-character-name", Static).update(profile.name)

        # Update emotional state from memory
        memory = self.state.get_selected_memory()
        if memory:
            self.query_one("#emotional-state", Static).update(
                memory.current_emotional_state
            )
            self.query_one("#memory-display", TextArea).text = memory.get_summary()
        else:
            self.query_one("#emotional-state", Static).update("neutral")
            self.query_one("#memory-display", TextArea).text = "No memory data"

        # Update chat display from conversation history
        chat_display = self.query_one("#chat-display", TextArea)
        chat_display.text = "\n".join(self.state.conversation_history)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-execute":
            self.action_execute()
        elif event.button.id == "btn-clear":
            self._clear_conversation()

    def _clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.state.conversation_history.clear()
        self.query_one("#chat-display", TextArea).text = ""
        self.query_one("#response-display", TextArea).text = ""
        self.notify("Conversation cleared")

    def action_execute(self) -> None:
        """Execute the current function."""
        if not self.state.selected_character:
            self.notify("No character selected", severity="error")
            return

        # Get or create the agent
        agent = self.state.get_or_create_agent(self.state.selected_character)
        if not agent:
            self.notify("Failed to create agent", severity="error")
            return

        select = self.query_one("#function-select", Select)
        function = select.value

        # Show loading state
        response_display = self.query_one("#response-display", TextArea)
        response_display.text = "Processing..."

        if function == self.FUNCTION_SPEAK:
            self._execute_speak(agent)
        elif function == self.FUNCTION_THINK:
            self._execute_think(agent)
        elif function == self.FUNCTION_CHOOSE:
            self._execute_choose(agent)
        elif function == self.FUNCTION_ANSWER:
            self._execute_answer(agent)

    def _execute_speak(self, agent) -> None:
        """Execute the speak function."""
        scene_context = self.query_one("#speak-scene-context", TextArea).text.strip()
        prompt = self.query_one("#speak-prompt", Input).value.strip()

        if not prompt:
            self.notify("Please enter a message", severity="error")
            return

        # Add user message to conversation history
        self.state.conversation_history.append(f"You: {prompt}")
        self.query_one("#chat-display", TextArea).text = "\n".join(
            self.state.conversation_history
        )

        # Build input
        speak_input = SpeakInput(
            scene_context=scene_context,
            conversation_history=self.state.conversation_history.copy(),
            prompt=prompt,
        )

        self._run_speak_worker(agent, speak_input)

    @work(thread=True)
    def _run_speak_worker(self, agent, speak_input: SpeakInput) -> None:
        """Run speak in a background thread."""
        worker = get_current_worker()
        try:
            response = agent.speak(speak_input)
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_speak_response, response)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_error, str(e))

    def _handle_speak_response(self, response: CharacterResponse) -> None:
        """Handle the speak response on the main thread."""
        character_name = self.state.selected_character or "Character"

        # Add character response to conversation history
        self.state.conversation_history.append(f"{character_name}: {response.content}")
        self.query_one("#chat-display", TextArea).text = "\n".join(
            self.state.conversation_history
        )

        # Clear the prompt input
        self.query_one("#speak-prompt", Input).value = ""

        # Update response display with metadata
        response_text = f"Emotional state: {response.emotional_state}"
        if response.internal_notes:
            response_text += f"\nInternal notes: {response.internal_notes}"
        self.query_one("#response-display", TextArea).text = response_text

        # Update memory display
        memory = self.state.get_selected_memory()
        if memory:
            self.query_one("#memory-display", TextArea).text = memory.get_summary()

        # Update emotional state display
        self.query_one("#emotional-state", Static).update(response.emotional_state)

    def _execute_think(self, agent) -> None:
        """Execute the think function."""
        scene_context = self.query_one("#think-scene-context", TextArea).text.strip()
        situation = self.query_one("#think-situation", TextArea).text.strip()

        if not situation:
            self.notify("Please describe the situation", severity="error")
            return

        think_input = ThinkInput(
            scene_context=scene_context,
            situation=situation,
        )

        self._run_think_worker(agent, think_input)

    @work(thread=True)
    def _run_think_worker(self, agent, think_input: ThinkInput) -> None:
        """Run think in a background thread."""
        worker = get_current_worker()
        try:
            response = agent.think(think_input)
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_generic_response, response, "thought")
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_error, str(e))

    def _execute_choose(self, agent) -> None:
        """Execute the choose function."""
        scene_context = self.query_one("#choose-scene-context", TextArea).text.strip()
        choices_text = self.query_one("#choose-choices", TextArea).text.strip()
        context = self.query_one("#choose-context", TextArea).text.strip()

        if not choices_text:
            self.notify("Please enter choices (one per line)", severity="error")
            return

        choices = [c.strip() for c in choices_text.split("\n") if c.strip()]
        if len(choices) < 2:
            self.notify("Please enter at least 2 choices", severity="error")
            return

        choose_input = ChooseInput(
            scene_context=scene_context,
            choices=choices,
            context=context,
        )

        self._run_choose_worker(agent, choose_input)

    @work(thread=True)
    def _run_choose_worker(self, agent, choose_input: ChooseInput) -> None:
        """Run choose in a background thread."""
        worker = get_current_worker()
        try:
            response = agent.choose(choose_input)
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_generic_response, response, "chose")
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_error, str(e))

    def _execute_answer(self, agent) -> None:
        """Execute the answer function."""
        question = self.query_one("#answer-question", Input).value.strip()
        asking_agent = self.query_one("#answer-asking-agent", Input).value.strip()
        context = self.query_one("#answer-context", TextArea).text.strip()

        if not question:
            self.notify("Please enter a question", severity="error")
            return

        answer_input = AnswerInput(
            question=question,
            asking_agent=asking_agent or "Unknown",
            context=context,
        )

        self._run_answer_worker(agent, answer_input)

    @work(thread=True)
    def _run_answer_worker(self, agent, answer_input: AnswerInput) -> None:
        """Run answer in a background thread."""
        worker = get_current_worker()
        try:
            response = agent.answer(answer_input)
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_generic_response, response, "answered")
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self._handle_error, str(e))

    def _handle_generic_response(
        self, response: CharacterResponse, action_type: str
    ) -> None:
        """Handle a generic response (think, choose, answer)."""
        response_text = f"[{action_type}]\n{response.content}"
        response_text += f"\n\nEmotional state: {response.emotional_state}"
        if response.internal_notes:
            response_text += f"\nInternal notes: {response.internal_notes}"

        self.query_one("#response-display", TextArea).text = response_text

        # Update memory display
        memory = self.state.get_selected_memory()
        if memory:
            self.query_one("#memory-display", TextArea).text = memory.get_summary()

        # Update emotional state display
        self.query_one("#emotional-state", Static).update(response.emotional_state)

    def _handle_error(self, error_message: str) -> None:
        """Handle an error response."""
        self.query_one("#response-display", TextArea).text = f"Error: {error_message}"
        self.notify(f"Error: {error_message}", severity="error")
