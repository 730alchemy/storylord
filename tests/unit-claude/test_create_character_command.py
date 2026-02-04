"""Unit tests for the /create-character command handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from slack_app.handlers.commands import handle_create_character
from slack_app.state import StateManager, WizardPhase


def _make_ack():
    """Return a mock ack callable that records whether it was called."""
    ack = MagicMock()
    return ack


def _make_say():
    """Return a mock say callable."""
    return MagicMock()


class TestCreateCharacterCommand:
    """Tests for the /create-character slash command handler."""

    def test_given_user_sends_create_character_command_when_handler_runs_then_state_set_to_WAITING_NAME(
        self,
    ):
        """Handler initialises the user's wizard state at WAITING_NAME."""
        manager = StateManager()
        ack = _make_ack()
        say = _make_say()

        handle_create_character(
            ack=ack,
            say=say,
            command={"user_id": "U123"},
            state_manager=manager,
        )

        state = manager.get("U123")
        assert state is not None
        assert state.phase == WizardPhase.WAITING_NAME

    def test_given_user_sends_create_character_command_when_handler_runs_then_ephemeral_message_asks_for_name(
        self,
    ):
        """Handler replies asking for the character's name."""
        manager = StateManager()
        ack = _make_ack()
        say = _make_say()

        handle_create_character(
            ack=ack,
            say=say,
            command={"user_id": "U123"},
            state_manager=manager,
        )

        ack.assert_called_once()
        say.assert_called_once()
        message = say.call_args[1].get("text", "") or say.call_args[0][0]
        assert "name" in message.lower()

    def test_given_user_with_active_session_sends_create_character_again_when_handler_runs_then_session_restarted(
        self,
    ):
        """A second /create-character discards the in-progress session (AC-28)."""
        manager = StateManager()
        ack = _make_ack()
        say = _make_say()

        # First invocation — advance state partway through the wizard
        handle_create_character(
            ack=ack, say=say, command={"user_id": "U123"}, state_manager=manager
        )
        manager.get("U123").phase = WizardPhase.WAITING_BACKSTORY
        manager.get("U123").name = "Half Finished"

        # Second invocation — should reset
        handle_create_character(
            ack=_make_ack(),
            say=_make_say(),
            command={"user_id": "U123"},
            state_manager=manager,
        )

        state = manager.get("U123")
        assert state.phase == WizardPhase.WAITING_NAME
        assert state.name == ""
