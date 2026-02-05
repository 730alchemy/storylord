"""Unit tests for Modal 2 (Agent Properties) — Slice 6."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.character.character_default import DEFAULT_PROPERTY_SCHEMA
from agents.character.character_mbti import MBTI_PROPERTY_SCHEMA
from slack_app.handlers.submissions import handle_modal_2_submit
from slack_app.modals import _schema_to_input_blocks, build_agent_properties_modal
from slack_app.state import StateManager, WizardPhase, WizardState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _submission_view(
    *,
    properties: dict[str, str],  # property_name → value_string
    instructions: str = "",
    channel_id: str = "D000",
) -> dict:
    """Build a minimal view dict for Modal 2 submission."""
    values = {}

    for prop_name, value_str in properties.items():
        values[f"{prop_name}_block"] = {f"{prop_name}_input": {"value": value_str}}

    values["agent_instructions_block"] = {
        "agent_instructions_input": {"value": instructions}
    }

    return {
        "state": {"values": values},
        "private_metadata": channel_id,
    }


def _body(user_id: str = "U1") -> dict:
    return {"user": {"id": user_id}}


# ---------------------------------------------------------------------------
# Tests: _schema_to_input_blocks converter
# ---------------------------------------------------------------------------


class TestSchemaToBlocks:
    """Verify the schema-to-blocks converter creates correct input blocks."""

    def test_creates_one_block_per_property(self):
        blocks = _schema_to_input_blocks(MBTI_PROPERTY_SCHEMA)
        assert len(blocks) == 4  # extroversion, intuition, thinking, judging

    def test_blocks_sorted_by_property_name(self):
        blocks = _schema_to_input_blocks(MBTI_PROPERTY_SCHEMA)
        block_ids = [b["block_id"] for b in blocks]
        assert block_ids == [
            "extroversion_block",
            "intuition_block",
            "judging_block",
            "thinking_block",
        ]

    def test_block_has_correct_structure(self):
        blocks = _schema_to_input_blocks(MBTI_PROPERTY_SCHEMA)
        block = blocks[0]  # extroversion
        assert block["type"] == "input"
        assert block["block_id"] == "extroversion_block"
        assert block["element"]["type"] == "plain_text_input"
        assert block["element"]["action_id"] == "extroversion_input"
        assert block["element"]["placeholder"]["text"] == "0-100"
        assert block["element"]["initial_value"] == "50"
        assert block["label"]["text"] == "Extroversion"
        assert "E/I dimension" in block["hint"]["text"]


# ---------------------------------------------------------------------------
# Tests: build_modal_2 — MBTI
# ---------------------------------------------------------------------------


class TestBuildModal2MBTI:
    """AC-18: Modal 2 for MBTI shows 4 numeric inputs + instructions."""

    def test_callback_id(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "D0")
        assert modal["callback_id"] == "modal_2_submit"

    def test_title(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "D0")
        assert modal["title"]["text"] == "Agent Properties"

    def test_submit_label(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "D0")
        assert modal["submit"]["text"] == "Next"

    def test_private_metadata_is_channel(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "DXYZ")
        assert modal["private_metadata"] == "DXYZ"

    def test_has_five_blocks(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "D0")
        # 4 properties + agent_instructions
        assert len(modal["blocks"]) == 5

    def test_property_blocks_for_mbti(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "D0")
        property_blocks = modal["blocks"][:4]
        block_ids = [b["block_id"] for b in property_blocks]
        assert block_ids == [
            "extroversion_block",
            "intuition_block",
            "judging_block",
            "thinking_block",
        ]

    def test_instructions_block_is_multiline_optional(self):
        modal = build_agent_properties_modal("mbti", MBTI_PROPERTY_SCHEMA, "D0")
        instructions_block = modal["blocks"][4]
        assert instructions_block["block_id"] == "agent_instructions_block"
        assert instructions_block["element"]["multiline"] is True
        assert instructions_block["optional"] is True


# ---------------------------------------------------------------------------
# Tests: build_modal_2 — Default
# ---------------------------------------------------------------------------


class TestBuildModal2Default:
    """AC-19: Modal 2 for default shows 5 numeric inputs + instructions."""

    def test_has_six_blocks(self):
        modal = build_agent_properties_modal("default", DEFAULT_PROPERTY_SCHEMA, "D0")
        # 5 properties + agent_instructions
        assert len(modal["blocks"]) == 6

    def test_property_blocks_for_default(self):
        modal = build_agent_properties_modal("default", DEFAULT_PROPERTY_SCHEMA, "D0")
        property_blocks = modal["blocks"][:5]
        block_ids = [b["block_id"] for b in property_blocks]
        assert block_ids == [
            "assertiveness_block",
            "emotionality_block",
            "formality_block",
            "verbosity_block",
            "warmth_block",
        ]

    def test_instructions_block_at_end(self):
        modal = build_agent_properties_modal("default", DEFAULT_PROPERTY_SCHEMA, "D0")
        instructions_block = modal["blocks"][5]
        assert instructions_block["block_id"] == "agent_instructions_block"


# ---------------------------------------------------------------------------
# Tests: handle_modal_2_submit — valid inputs  (AC-21)
# ---------------------------------------------------------------------------


class TestModal2SubmitValid:
    """AC-21: Valid submission stores properties and advances to PREVIEW."""

    def setup_method(self):
        self.sm = StateManager()
        state = WizardState(phase=WizardPhase.MODAL_2_OPEN, name="Aria")
        state.agent_type = "mbti"
        self.sm.set("U1", state)
        self.ack = MagicMock()
        self.client = MagicMock()

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_phase_advances_to_preview(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "60",
                    "intuition": "70",
                    "thinking": "80",
                    "judging": "90",
                },
                instructions="Be creative",
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").phase == WizardPhase.PREVIEW

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_agent_properties_stored(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "60",
                    "intuition": "70",
                    "thinking": "80",
                    "judging": "90",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        props = self.sm.get("U1").agent_properties
        assert props["extroversion"] == 60.0
        assert props["intuition"] == 70.0
        assert props["thinking"] == 80.0
        assert props["judging"] == 90.0

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_agent_instructions_stored(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                },
                instructions="Be whimsical and playful",
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").agent_instructions == "Be whimsical and playful"

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_empty_instructions_stored_as_empty_string(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                },
                instructions="",
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").agent_instructions == ""

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_ack_called_with_no_errors(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        self.ack.assert_called_once_with()

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_posts_message_to_dm(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                },
                channel_id="DABC",
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        self.client.chat_postMessage.assert_called_once()
        assert self.client.chat_postMessage.call_args[1]["channel"] == "DABC"


# ---------------------------------------------------------------------------
# Tests: handle_modal_2_submit — validation errors  (AC-20)
# ---------------------------------------------------------------------------


class TestModal2SubmitValidation:
    """AC-20: Out-of-range or non-numeric values show validation errors."""

    def setup_method(self):
        self.sm = StateManager()
        state = WizardState(phase=WizardPhase.MODAL_2_OPEN, name="Aria")
        state.agent_type = "mbti"
        self.sm.set("U1", state)
        self.ack = MagicMock()
        self.client = MagicMock()

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_value_above_100_shows_error(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "150",  # out of range
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        self.ack.assert_called_once()
        call_kwargs = self.ack.call_args[1]
        assert call_kwargs["response_action"] == "errors"
        assert "extroversion_block" in call_kwargs["errors"]
        assert "0 and 100" in call_kwargs["errors"]["extroversion_block"]

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_value_below_0_shows_error(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "-10",  # out of range
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        call_kwargs = self.ack.call_args[1]
        assert "intuition_block" in call_kwargs["errors"]

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_non_numeric_value_shows_error(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "50",
                    "thinking": "abc",  # not a number
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        call_kwargs = self.ack.call_args[1]
        assert "thinking_block" in call_kwargs["errors"]
        assert "number" in call_kwargs["errors"]["thinking_block"]

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_multiple_errors_all_shown(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "150",  # out of range
                    "intuition": "xyz",  # not a number
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        call_kwargs = self.ack.call_args[1]
        errors = call_kwargs["errors"]
        assert "extroversion_block" in errors
        assert "intuition_block" in errors

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_validation_error_does_not_advance_phase(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "150",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        # Phase should remain MODAL_2_OPEN (not advanced to PREVIEW)
        assert self.sm.get("U1").phase == WizardPhase.MODAL_2_OPEN

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_validation_error_does_not_post_message(self, mock_get):
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = MBTI_PROPERTY_SCHEMA
        mock_get.return_value = mock_agent_type

        handle_modal_2_submit(
            ack=self.ack,
            view=_submission_view(
                properties={
                    "extroversion": "150",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        self.client.chat_postMessage.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: handle_modal_2_submit — edge cases
# ---------------------------------------------------------------------------


class TestModal2NoSession:
    """Submission when the user has no active wizard session."""

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_ack_called_and_no_crash(self, mock_get):
        sm = StateManager()
        ack = MagicMock()
        client = MagicMock()

        handle_modal_2_submit(
            ack=ack,
            view=_submission_view(
                properties={
                    "extroversion": "50",
                    "intuition": "50",
                    "thinking": "50",
                    "judging": "50",
                }
            ),
            body=_body("U_UNKNOWN"),
            state_manager=sm,
            client=client,
        )

        ack.assert_called_once_with()
        # get_character_agent_type should not be called if no session
        mock_get.assert_not_called()
