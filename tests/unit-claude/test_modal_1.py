"""Unit tests for Modal 1 (Role and Agent Config Toggle) — Slice 5."""

from __future__ import annotations

from unittest.mock import MagicMock

from slack_app.handlers.submissions import handle_modal_1_submit
from slack_app.modals import ROLE_OPTIONS, build_character_setup_modal
from slack_app.state import StateManager, WizardPhase, WizardState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_agent_types(*names: str) -> dict[str, MagicMock]:
    """Return a dict of agent-type name → stub, suitable for build_modal_1."""
    return {name: MagicMock() for name in names}


def _submission_view(
    *,
    role: str = "supporting",
    toggle_on: bool = False,
    agent_type: str = "default",
    channel_id: str = "D000",
) -> dict:
    """Minimal view dict mirroring what Slack sends in a view_submission."""
    toggle_options = [{"value": "enabled"}] if toggle_on else []
    return {
        "state": {
            "values": {
                "role_block": {"role_select": {"selected_option": {"value": role}}},
                "agent_toggle_block": {
                    "agent_toggle": {"selected_options": toggle_options}
                },
                "agent_type_block": {
                    "agent_type_select": {"selected_option": {"value": agent_type}}
                },
            }
        },
        "private_metadata": channel_id,
    }


def _body(user_id: str = "U1") -> dict:
    return {"user": {"id": user_id}}


# ---------------------------------------------------------------------------
# Tests: build_modal_1 structure
# ---------------------------------------------------------------------------


class TestBuildModal1Structure:
    """Verify the static structure of Modal 1."""

    def test_callback_id(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        assert modal["callback_id"] == "modal_1_submit"

    def test_title(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        assert modal["title"]["text"] == "Character Setup"

    def test_submit_label(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        assert modal["submit"]["text"] == "Next"

    def test_private_metadata_is_channel(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="DXYZ"
        )
        assert modal["private_metadata"] == "DXYZ"

    def test_has_three_blocks(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        assert len(modal["blocks"]) == 3

    def test_role_block(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        block = modal["blocks"][0]
        assert block["block_id"] == "role_block"
        assert block["element"]["type"] == "static_select"
        assert block["element"]["action_id"] == "role_select"
        assert block["element"]["options"] == ROLE_OPTIONS

    def test_toggle_block_is_optional(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        block = modal["blocks"][1]
        assert block["block_id"] == "agent_toggle_block"
        assert block["element"]["type"] == "checkboxes"
        assert block["element"]["action_id"] == "agent_toggle"
        assert block["optional"] is True

    def test_toggle_block_single_option(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        options = modal["blocks"][1]["element"]["options"]
        assert len(options) == 1
        assert options[0]["value"] == "enabled"

    def test_agent_type_block(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        block = modal["blocks"][2]
        assert block["block_id"] == "agent_type_block"
        assert block["element"]["type"] == "static_select"
        assert block["element"]["action_id"] == "agent_type_select"


# ---------------------------------------------------------------------------
# Tests: build_modal_1 dynamic agent-type options  (AC-17)
# ---------------------------------------------------------------------------


class TestBuildModal1DynamicOptions:
    """AC-17: agent_type dropdown is populated from discover results."""

    def test_single_agent_type(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("default"), channel_id="D0"
        )
        options = modal["blocks"][2]["element"]["options"]
        assert len(options) == 1
        assert options[0]["value"] == "default"

    def test_multiple_agent_types_sorted(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("mbti", "default", "zodiac"),
            channel_id="D0",
        )
        options = modal["blocks"][2]["element"]["options"]
        values = [o["value"] for o in options]
        assert values == ["default", "mbti", "zodiac"]

    def test_option_text_matches_name(self):
        modal = build_character_setup_modal(
            agent_types=_fake_agent_types("mbti"), channel_id="D0"
        )
        option = modal["blocks"][2]["element"]["options"][0]
        assert option["text"]["text"] == "mbti"
        assert option["text"]["type"] == "plain_text"


# ---------------------------------------------------------------------------
# Tests: handle_modal_1_submit — toggle OFF  (AC-15)
# ---------------------------------------------------------------------------


class TestModal1ToggleOff:
    """AC-15: toggle off → PREVIEW, agent_config stays None."""

    def setup_method(self):
        self.sm = StateManager()
        self.sm.set("U1", WizardState(phase=WizardPhase.MODAL_1_OPEN, name="Aria"))
        self.ack = MagicMock()
        self.client = MagicMock()

    def _submit(self, role: str = "antagonist") -> None:
        handle_modal_1_submit(
            ack=self.ack,
            view=_submission_view(role=role, toggle_on=False),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

    def test_phase_advances_to_preview(self):
        self._submit()
        assert self.sm.get("U1").phase == WizardPhase.PREVIEW

    def test_role_stored(self):
        self._submit(role="protagonist")
        assert self.sm.get("U1").role == "protagonist"

    def test_agent_config_enabled_is_false(self):
        self._submit()
        assert self.sm.get("U1").agent_config_enabled is False

    def test_ack_called(self):
        self._submit()
        self.ack.assert_called_once()

    def test_posts_message_to_dm(self):
        self._submit()
        self.client.chat_postMessage.assert_called_once()
        assert self.client.chat_postMessage.call_args[1]["channel"] == "D000"


# ---------------------------------------------------------------------------
# Tests: handle_modal_1_submit — toggle ON  (AC-16)
# ---------------------------------------------------------------------------


class TestModal1ToggleOn:
    """AC-16: toggle on → MODAL_2_OPEN, agent_type stored."""

    def setup_method(self):
        self.sm = StateManager()
        self.sm.set("U1", WizardState(phase=WizardPhase.MODAL_1_OPEN, name="Aria"))
        self.ack = MagicMock()
        self.client = MagicMock()

    def _submit(self, role: str = "minor", agent_type: str = "mbti") -> None:
        handle_modal_1_submit(
            ack=self.ack,
            view=_submission_view(role=role, toggle_on=True, agent_type=agent_type),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

    def test_phase_advances_to_modal_2(self):
        self._submit()
        assert self.sm.get("U1").phase == WizardPhase.MODAL_2_OPEN

    def test_agent_type_stored(self):
        self._submit(agent_type="mbti")
        assert self.sm.get("U1").agent_type == "mbti"

    def test_agent_config_enabled_is_true(self):
        self._submit()
        assert self.sm.get("U1").agent_config_enabled is True

    def test_role_stored(self):
        self._submit(role="minor")
        assert self.sm.get("U1").role == "minor"

    def test_ack_called(self):
        self._submit()
        self.ack.assert_called_once()

    def test_posts_message_to_dm(self):
        self._submit()
        self.client.chat_postMessage.assert_called_once()
        assert self.client.chat_postMessage.call_args[1]["channel"] == "D000"


# ---------------------------------------------------------------------------
# Tests: handle_modal_1_submit — edge cases
# ---------------------------------------------------------------------------


class TestModal1NoSession:
    """Submission when the user has no active wizard session."""

    def test_ack_called_and_no_crash(self):
        sm = StateManager()
        ack = MagicMock()
        client = MagicMock()
        handle_modal_1_submit(
            ack=ack,
            view=_submission_view(),
            body=_body("U_UNKNOWN"),
            state_manager=sm,
            client=client,
        )
        ack.assert_called_once()

    def test_no_message_posted_when_no_session(self):
        sm = StateManager()
        ack = MagicMock()
        client = MagicMock()
        handle_modal_1_submit(
            ack=ack,
            view=_submission_view(),
            body=_body("U_UNKNOWN"),
            state_manager=sm,
            client=client,
        )
        client.chat_postMessage.assert_not_called()
