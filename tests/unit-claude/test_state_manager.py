"""Unit tests for StateManager."""

from __future__ import annotations

from slack_app.state import StateManager, WizardPhase, WizardState


class TestStateManager:
    """Tests for StateManager get/set/clear/start_new."""

    def test_given_no_state_for_user_when_get_called_then_returns_None(self):
        """A user with no session returns None."""
        manager = StateManager()

        assert manager.get("unknown-user") is None

    def test_given_state_set_for_user_when_get_called_then_returns_that_state(self):
        """get() returns the exact state that was set."""
        manager = StateManager()
        state = WizardState(phase=WizardPhase.WAITING_DESCRIPTION, name="Test")
        manager.set("user-1", state)

        result = manager.get("user-1")

        assert result is state
        assert result.name == "Test"
        assert result.phase == WizardPhase.WAITING_DESCRIPTION

    def test_given_state_exists_for_user_when_clear_called_then_get_returns_None(self):
        """clear() removes the user's state entirely."""
        manager = StateManager()
        manager.set("user-1", WizardState(phase=WizardPhase.WAITING_NAME))

        manager.clear("user-1")

        assert manager.get("user-1") is None

    def test_given_no_prior_state_when_start_new_called_then_returns_state_at_WAITING_NAME(
        self,
    ):
        """start_new() on a fresh user returns a state at WAITING_NAME."""
        manager = StateManager()

        state = manager.start_new("user-1")

        assert state.phase == WizardPhase.WAITING_NAME
        assert manager.get("user-1") is state

    def test_given_active_session_when_start_new_called_then_old_state_discarded_and_fresh_state_returned(
        self,
    ):
        """start_new() discards an in-progress session and returns a clean slate (AC-28)."""
        manager = StateManager()
        old = manager.start_new("user-1")
        old.name = "Half Finished"
        old.phase = WizardPhase.WAITING_BACKSTORY

        new = manager.start_new("user-1")

        assert new.phase == WizardPhase.WAITING_NAME
        assert new.name == ""
        assert new is not old

    def test_given_states_for_multiple_users_when_one_cleared_then_others_unaffected(
        self,
    ):
        """State is isolated per user_id — clearing one doesn't touch another."""
        manager = StateManager()
        manager.start_new("user-1")
        manager.start_new("user-2")

        manager.clear("user-1")

        assert manager.get("user-1") is None
        assert manager.get("user-2") is not None
