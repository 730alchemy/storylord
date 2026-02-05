"""Unit tests for Preview and Save — Slice 7."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from slack_app.handlers.actions import handle_save_action
from slack_app.state import StateManager, WizardPhase, WizardState
from slack_app.views import build_confirmation_message, build_preview_message


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _body(user_id: str = "U1", channel_id: str = "D000") -> dict:
    """Minimal action body dict."""
    return {"user": {"id": user_id}, "channel": {"id": channel_id}}


def _sample_state() -> WizardState:
    """Return a complete wizard state ready for preview."""
    return WizardState(
        phase=WizardPhase.PREVIEW,
        name="Aria Flynn",
        description="A sharp-witted detective",
        motivations="Uncover the truth",
        backstory="Former journalist turned PI",
        relationships="Close to her sister, estranged from father",
        role="protagonist",
        agent_config_enabled=True,
        agent_type="default",
        agent_properties={
            "assertiveness": 75.0,
            "warmth": 50.0,
            "formality": 40.0,
            "verbosity": 60.0,
            "emotionality": 55.0,
        },
        agent_instructions="Be witty and observant",
    )


# ---------------------------------------------------------------------------
# Tests: build_preview_message structure (AC-22, AC-23)
# ---------------------------------------------------------------------------


class TestBuildPreviewMessage:
    """Verify the structure and content of the preview message."""

    def test_has_text_field(self):
        state = _sample_state()
        msg = build_preview_message(state)
        assert "text" in msg
        assert msg["text"] == "Here's your character preview:"

    def test_has_blocks(self):
        state = _sample_state()
        msg = build_preview_message(state)
        assert "blocks" in msg
        assert len(msg["blocks"]) == 3  # section, code block, actions

    def test_first_block_is_section_with_text(self):
        state = _sample_state()
        msg = build_preview_message(state)
        block = msg["blocks"][0]
        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"
        assert "character preview" in block["text"]["text"]

    def test_second_block_contains_yaml_code_block(self):
        state = _sample_state()
        msg = build_preview_message(state)
        block = msg["blocks"][1]
        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"
        text = block["text"]["text"]
        assert text.startswith("```yaml\n")
        assert text.endswith("\n```")

    def test_yaml_contains_character_name(self):
        state = _sample_state()
        msg = build_preview_message(state)
        yaml_text = msg["blocks"][1]["text"]["text"]
        assert "Aria Flynn" in yaml_text

    def test_yaml_contains_role(self):
        state = _sample_state()
        msg = build_preview_message(state)
        yaml_text = msg["blocks"][1]["text"]["text"]
        assert "protagonist" in yaml_text

    def test_yaml_contains_agent_config_when_enabled(self):
        state = _sample_state()
        msg = build_preview_message(state)
        yaml_text = msg["blocks"][1]["text"]["text"]
        assert "agent_config" in yaml_text
        assert "default" in yaml_text  # agent_type
        assert "assertiveness" in yaml_text

    def test_yaml_excludes_agent_config_when_disabled(self):
        state = _sample_state()
        state.agent_config_enabled = False
        msg = build_preview_message(state)
        yaml_text = msg["blocks"][1]["text"]["text"]
        assert "agent_config" not in yaml_text

    def test_third_block_is_actions(self):
        state = _sample_state()
        msg = build_preview_message(state)
        block = msg["blocks"][2]
        assert block["type"] == "actions"

    def test_has_save_button(self):
        state = _sample_state()
        msg = build_preview_message(state)
        actions = msg["blocks"][2]["elements"]
        save_btn = next(
            (b for b in actions if b["action_id"] == "save_character"), None
        )
        assert save_btn is not None
        assert save_btn["type"] == "button"
        assert save_btn["text"]["text"] == "Save"
        assert save_btn["style"] == "primary"

    def test_has_edit_button(self):
        state = _sample_state()
        msg = build_preview_message(state)
        actions = msg["blocks"][2]["elements"]
        edit_btn = next(
            (b for b in actions if b["action_id"] == "edit_character"), None
        )
        assert edit_btn is not None
        assert edit_btn["type"] == "button"
        assert edit_btn["text"]["text"] == "Edit"


# ---------------------------------------------------------------------------
# Tests: build_confirmation_message (AC-26)
# ---------------------------------------------------------------------------


class TestBuildConfirmationMessage:
    """Verify the confirmation message after save."""

    def test_has_text_field_with_path(self):
        path = Path("/home/user/character_library/aria-flynn.yaml")
        msg = build_confirmation_message(path)
        assert "text" in msg
        assert str(path) in msg["text"]

    def test_has_blocks(self):
        path = Path("/home/user/character_library/aria-flynn.yaml")
        msg = build_confirmation_message(path)
        assert "blocks" in msg
        assert len(msg["blocks"]) == 1

    def test_block_is_section_with_checkmark(self):
        path = Path("/home/user/character_library/aria-flynn.yaml")
        msg = build_confirmation_message(path)
        block = msg["blocks"][0]
        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"
        assert "✅" in block["text"]["text"]
        assert "Character saved" in block["text"]["text"]
        assert str(path) in block["text"]["text"]


# ---------------------------------------------------------------------------
# Tests: handle_save_action (AC-26, AC-27)
# ---------------------------------------------------------------------------


class TestHandleSaveAction:
    """Test the Save button action handler."""

    def setup_method(self):
        self.sm = StateManager()
        self.ack = MagicMock()
        self.client = MagicMock()

    @patch("slack_app.handlers.actions.CharacterStore")
    def test_saves_profile_via_character_store(self, mock_store_class):
        state = _sample_state()
        self.sm.set("U1", state)
        mock_store_instance = MagicMock()
        mock_store_class.return_value = mock_store_instance
        mock_store_instance.save.return_value = Path("/tmp/aria-flynn.yaml")

        handle_save_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        # Verify CharacterStore was instantiated with library dir
        mock_store_class.assert_called_once()
        # Verify save was called with a CharacterProfile
        mock_store_instance.save.assert_called_once()
        profile = mock_store_instance.save.call_args[0][0]
        assert profile.name == "Aria Flynn"
        assert profile.role == "protagonist"

    @patch("slack_app.handlers.actions.CharacterStore")
    def test_posts_confirmation_message(self, mock_store_class):
        state = _sample_state()
        self.sm.set("U1", state)
        mock_store_instance = MagicMock()
        mock_store_class.return_value = mock_store_instance
        saved_path = Path("/tmp/aria-flynn.yaml")
        mock_store_instance.save.return_value = saved_path

        handle_save_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        self.client.chat_postMessage.assert_called_once()
        call_kwargs = self.client.chat_postMessage.call_args[1]
        assert call_kwargs["channel"] == "D000"
        assert str(saved_path) in call_kwargs["text"]

    @patch("slack_app.handlers.actions.CharacterStore")
    def test_clears_state_after_save(self, mock_store_class):
        state = _sample_state()
        self.sm.set("U1", state)
        mock_store_instance = MagicMock()
        mock_store_class.return_value = mock_store_instance
        mock_store_instance.save.return_value = Path("/tmp/aria-flynn.yaml")

        handle_save_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        # State should be cleared (AC-27)
        assert self.sm.get("U1") is None

    @patch("slack_app.handlers.actions.CharacterStore")
    def test_ack_called(self, mock_store_class):
        state = _sample_state()
        self.sm.set("U1", state)
        mock_store_instance = MagicMock()
        mock_store_class.return_value = mock_store_instance
        mock_store_instance.save.return_value = Path("/tmp/aria-flynn.yaml")

        handle_save_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        self.ack.assert_called_once()

    def test_no_session_acks_and_posts_guidance(self):
        # No state set for U1
        handle_save_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        self.ack.assert_called_once()
        self.client.chat_postMessage.assert_called_once()
        call_kwargs = self.client.chat_postMessage.call_args[1]
        assert call_kwargs["channel"] == "D000"
        assert "/create-character" in call_kwargs["text"]

    @patch("slack_app.handlers.actions.CharacterStore")
    def test_agent_config_none_when_disabled(self, mock_store_class):
        state = _sample_state()
        state.agent_config_enabled = False
        self.sm.set("U1", state)
        mock_store_instance = MagicMock()
        mock_store_class.return_value = mock_store_instance
        mock_store_instance.save.return_value = Path("/tmp/aria-flynn.yaml")

        handle_save_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        profile = mock_store_instance.save.call_args[0][0]
        assert profile.agent_config is None
