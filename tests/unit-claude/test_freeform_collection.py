"""Unit tests for the DM freeform field collection handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from slack_app.handlers.messages import handle_message
from slack_app.state import StateManager, WizardPhase


def _make_say() -> MagicMock:
    return MagicMock()


def _dm(user_id: str, text: str) -> dict:
    """Minimal DM message payload."""
    return {"user": user_id, "text": text, "channel_type": "im"}


class TestNameCapture:
    """WAITING_NAME phase captures the name and advances."""

    def test_given_WAITING_NAME_when_name_sent_then_name_captured(self):
        manager = StateManager()
        manager.start_new("U1")

        handle_message(
            message=_dm("U1", "Elijah"), say=_make_say(), state_manager=manager
        )

        assert manager.get("U1").name == "Elijah"

    def test_given_WAITING_NAME_when_name_sent_then_phase_advances_to_WAITING_DESCRIPTION(
        self,
    ):
        manager = StateManager()
        manager.start_new("U1")

        handle_message(
            message=_dm("U1", "Elijah"), say=_make_say(), state_manager=manager
        )

        assert manager.get("U1").phase == WizardPhase.WAITING_DESCRIPTION

    def test_given_WAITING_NAME_when_name_sent_then_say_asks_for_description_using_name(
        self,
    ):
        manager = StateManager()
        manager.start_new("U1")
        say = _make_say()

        handle_message(message=_dm("U1", "Elijah"), say=say, state_manager=manager)

        say.assert_called_once()
        reply = say.call_args[1]["text"]
        assert "elijah" in reply.lower()
        assert "describe" in reply.lower()


class TestMiddlePhases:
    """Each middle phase captures its field and advances correctly."""

    def _seed(self, manager: StateManager, phase: WizardPhase) -> None:
        state = manager.start_new("U1")
        state.phase = phase
        state.name = "Elijah"

    def test_given_WAITING_DESCRIPTION_when_text_sent_then_captured_and_advances(self):
        manager = StateManager()
        self._seed(manager, WizardPhase.WAITING_DESCRIPTION)

        handle_message(
            message=_dm("U1", "A wandering scholar"),
            say=_make_say(),
            state_manager=manager,
        )

        assert manager.get("U1").description == "A wandering scholar"
        assert manager.get("U1").phase == WizardPhase.WAITING_MOTIVATIONS

    def test_given_WAITING_MOTIVATIONS_when_text_sent_then_captured_and_advances(self):
        manager = StateManager()
        self._seed(manager, WizardPhase.WAITING_MOTIVATIONS)

        handle_message(
            message=_dm("U1", "Seeks knowledge"),
            say=_make_say(),
            state_manager=manager,
        )

        assert manager.get("U1").motivations == "Seeks knowledge"
        assert manager.get("U1").phase == WizardPhase.WAITING_BACKSTORY

    def test_given_WAITING_BACKSTORY_when_text_sent_then_captured_and_advances(self):
        manager = StateManager()
        self._seed(manager, WizardPhase.WAITING_BACKSTORY)

        handle_message(
            message=_dm("U1", "Raised in a village"),
            say=_make_say(),
            state_manager=manager,
        )

        assert manager.get("U1").backstory == "Raised in a village"
        assert manager.get("U1").phase == WizardPhase.WAITING_RELATIONSHIPS


class TestRelationships:
    """WAITING_RELATIONSHIPS: capture text or honour "skip"."""

    def _seed(self, manager: StateManager) -> None:
        state = manager.start_new("U1")
        state.phase = WizardPhase.WAITING_RELATIONSHIPS
        state.name = "Elijah"

    def test_given_WAITING_RELATIONSHIPS_when_text_sent_then_captured_and_advances_to_MODAL_1(
        self,
    ):
        manager = StateManager()
        self._seed(manager)

        handle_message(
            message=_dm("U1", "Friends with Riley"),
            say=_make_say(),
            state_manager=manager,
        )

        assert manager.get("U1").relationships == "Friends with Riley"
        assert manager.get("U1").phase == WizardPhase.MODAL_1_OPEN

    def test_given_WAITING_RELATIONSHIPS_when_skip_lowercase_sent_then_relationships_empty(
        self,
    ):
        manager = StateManager()
        self._seed(manager)

        handle_message(
            message=_dm("U1", "skip"), say=_make_say(), state_manager=manager
        )

        assert manager.get("U1").relationships == ""
        assert manager.get("U1").phase == WizardPhase.MODAL_1_OPEN

    def test_given_WAITING_RELATIONSHIPS_when_SKIP_uppercase_sent_then_relationships_empty(
        self,
    ):
        manager = StateManager()
        self._seed(manager)

        handle_message(
            message=_dm("U1", "SKIP"), say=_make_say(), state_manager=manager
        )

        assert manager.get("U1").relationships == ""
        assert manager.get("U1").phase == WizardPhase.MODAL_1_OPEN


class TestEdgeCases:
    """No active session, bad input, wrong channel, wrong phase."""

    def test_given_no_active_session_when_dm_received_then_say_guides_to_create_character(
        self,
    ):
        manager = StateManager()
        say = _make_say()

        handle_message(message=_dm("U1", "hello"), say=say, state_manager=manager)

        say.assert_called_once()
        assert "/create-character" in say.call_args[1]["text"]

    def test_given_message_with_no_text_when_in_freeform_phase_then_say_gives_guidance(
        self,
    ):
        manager = StateManager()
        manager.start_new("U1")  # WAITING_NAME
        say = _make_say()
        attachment_msg = {"user": "U1", "channel_type": "im"}  # no "text" key

        handle_message(message=attachment_msg, say=say, state_manager=manager)

        say.assert_called_once()
        assert "name" in say.call_args[1]["text"].lower()

    def test_given_non_dm_message_when_handler_runs_then_say_not_called(self):
        manager = StateManager()
        manager.start_new("U1")
        say = _make_say()

        handle_message(
            message={"user": "U1", "text": "hi", "channel_type": "channel"},
            say=say,
            state_manager=manager,
        )

        say.assert_not_called()

    def test_given_user_in_MODAL_1_OPEN_when_dm_sent_then_say_guides_to_form(self):
        manager = StateManager()
        state = manager.start_new("U1")
        state.phase = WizardPhase.MODAL_1_OPEN
        say = _make_say()

        handle_message(message=_dm("U1", "anything"), say=say, state_manager=manager)

        say.assert_called_once()
        assert "form" in say.call_args[1]["text"].lower()

    def test_given_message_with_subtype_when_handler_runs_then_say_not_called(self):
        manager = StateManager()
        manager.start_new("U1")
        say = _make_say()

        handle_message(
            message={
                "user": "U1",
                "text": "hi",
                "channel_type": "im",
                "subtype": "bot_message",
            },
            say=say,
            state_manager=manager,
        )

        say.assert_not_called()
