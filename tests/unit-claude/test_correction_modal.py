"""Unit tests for Correction Modal (Edit flow) — Slice 8."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from slack_app.handlers.actions import handle_edit_action
from slack_app.handlers.submissions import handle_correction_modal_submit
from slack_app.modals import build_correction_modal
from slack_app.state import StateManager, WizardPhase, WizardState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_agent_types(*names: str) -> dict[str, MagicMock]:
    """Return a dict of agent-type name → stub."""
    types = {}
    for name in names:
        mock_type = MagicMock()
        mock_type.property_schema = {
            "properties": {
                "prop_a": {
                    "type": "number",
                    "default": 50,
                    "description": "Property A",
                },
                "prop_b": {
                    "type": "number",
                    "default": 50,
                    "description": "Property B",
                },
            }
        }
        types[name] = mock_type
    return types


def _sample_property_schema() -> dict:
    """Return a sample property schema for testing."""
    return {
        "properties": {
            "assertiveness": {
                "type": "number",
                "default": 50,
                "description": "How assertive",
            },
            "warmth": {"type": "number", "default": 50, "description": "How warm"},
        }
    }


def _complete_state() -> WizardState:
    """Return a complete wizard state with all fields filled."""
    return WizardState(
        phase=WizardPhase.PREVIEW,
        name="Aria Flynn",
        description="A sharp detective",
        motivations="Find the truth",
        backstory="Former journalist",
        relationships="Sister: close; Father: estranged",
        role="protagonist",
        agent_config_enabled=True,
        agent_type="default",
        agent_properties={"assertiveness": 75.0, "warmth": 60.0},
        agent_instructions="Be observant and witty",
    )


def _correction_view(
    *,
    name: str = "Updated Name",
    description: str = "Updated desc",
    motivations: str = "Updated motivations",
    backstory: str = "Updated backstory",
    relationships: str = "Updated relationships",
    role: str = "antagonist",
    toggle_on: bool = True,
    agent_type: str = "default",
    prop_a: str = "80",
    prop_b: str = "70",
    agent_instructions: str = "Updated instructions",
    channel_id: str = "D000",
) -> dict:
    """Minimal view dict for correction modal submission."""
    toggle_options = [{"value": "enabled"}] if toggle_on else []
    return {
        "state": {
            "values": {
                "name_block": {"name_input": {"value": name}},
                "description_block": {"description_input": {"value": description}},
                "motivations_block": {"motivations_input": {"value": motivations}},
                "backstory_block": {"backstory_input": {"value": backstory}},
                "relationships_block": {
                    "relationships_input": {"value": relationships}
                },
                "role_block": {"role_select": {"selected_option": {"value": role}}},
                "agent_toggle_block": {
                    "agent_toggle": {"selected_options": toggle_options}
                },
                "agent_type_block": {
                    "agent_type_select": {"selected_option": {"value": agent_type}}
                },
                "prop_a_block": {"prop_a_input": {"value": prop_a}},
                "prop_b_block": {"prop_b_input": {"value": prop_b}},
                "agent_instructions_block": {
                    "agent_instructions_input": {"value": agent_instructions}
                },
            }
        },
        "private_metadata": channel_id,
    }


def _body(user_id: str = "U1", channel_id: str = "D000") -> dict:
    """Minimal body dict."""
    return {
        "user": {"id": user_id},
        "channel": {"id": channel_id},
        "trigger_id": "trigger_123",
    }


# ---------------------------------------------------------------------------
# Tests: build_correction_modal structure (AC-24)
# ---------------------------------------------------------------------------


class TestBuildCorrectionModalStructure:
    """Verify the structure of the correction modal."""

    def test_callback_id(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        assert modal["callback_id"] == "correction_modal_submit"

    def test_title(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        assert modal["title"]["text"] == "Edit Character"

    def test_submit_label(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        assert modal["submit"]["text"] == "Update"

    def test_has_all_field_blocks(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        block_ids = [b["block_id"] for b in modal["blocks"]]
        # Freeform fields
        assert "name_block" in block_ids
        assert "description_block" in block_ids
        assert "motivations_block" in block_ids
        assert "backstory_block" in block_ids
        assert "relationships_block" in block_ids
        # Modal 1 fields
        assert "role_block" in block_ids
        assert "agent_toggle_block" in block_ids
        assert "agent_type_block" in block_ids
        # Modal 2 fields (dynamic based on schema)
        assert "assertiveness_block" in block_ids
        assert "warmth_block" in block_ids
        assert "agent_instructions_block" in block_ids


# ---------------------------------------------------------------------------
# Tests: field pre-population (AC-24)
# ---------------------------------------------------------------------------


class TestCorrectionModalPrePopulation:
    """Verify all fields are pre-populated from state."""

    def test_name_pre_populated(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        name_block = next(b for b in modal["blocks"] if b["block_id"] == "name_block")
        assert name_block["element"]["initial_value"] == "Aria Flynn"

    def test_description_pre_populated(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        desc_block = next(
            b for b in modal["blocks"] if b["block_id"] == "description_block"
        )
        assert desc_block["element"]["initial_value"] == "A sharp detective"

    def test_role_pre_selected(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        role_block = next(b for b in modal["blocks"] if b["block_id"] == "role_block")
        assert role_block["element"]["initial_option"]["value"] == "protagonist"

    def test_agent_toggle_checked_when_enabled(self):
        state = _complete_state()
        state.agent_config_enabled = True
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        toggle_block = next(
            b for b in modal["blocks"] if b["block_id"] == "agent_toggle_block"
        )
        assert len(toggle_block["element"]["initial_options"]) == 1
        assert toggle_block["element"]["initial_options"][0]["value"] == "enabled"

    def test_agent_toggle_unchecked_when_disabled(self):
        state = _complete_state()
        state.agent_config_enabled = False
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        toggle_block = next(
            b for b in modal["blocks"] if b["block_id"] == "agent_toggle_block"
        )
        assert toggle_block["element"]["initial_options"] == []

    def test_agent_type_pre_selected(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default", "mbti"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        agent_type_block = next(
            b for b in modal["blocks"] if b["block_id"] == "agent_type_block"
        )
        assert agent_type_block["element"]["initial_option"]["value"] == "default"

    def test_agent_properties_pre_populated(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        assertiveness_block = next(
            b for b in modal["blocks"] if b["block_id"] == "assertiveness_block"
        )
        assert assertiveness_block["element"]["initial_value"] == "75.0"

    def test_agent_instructions_pre_populated(self):
        state = _complete_state()
        modal = build_correction_modal(
            state=state,
            agent_types=_fake_agent_types("default"),
            property_schema=_sample_property_schema(),
            channel_id="D0",
        )
        instructions_block = next(
            b for b in modal["blocks"] if b["block_id"] == "agent_instructions_block"
        )
        assert (
            instructions_block["element"]["initial_value"] == "Be observant and witty"
        )


# ---------------------------------------------------------------------------
# Tests: handle_edit_action
# ---------------------------------------------------------------------------


class TestHandleEditAction:
    """Test the Edit button action handler."""

    def setup_method(self):
        self.sm = StateManager()
        self.ack = MagicMock()
        self.client = MagicMock()

    @patch("slack_app.handlers.actions.discover_character_agent_types")
    @patch("slack_app.handlers.actions.get_character_agent_type")
    def test_opens_correction_modal(
        self, mock_get_agent_type, mock_discover_agent_types
    ):
        state = _complete_state()
        self.sm.set("U1", state)

        mock_discover_agent_types.return_value = _fake_agent_types("default")
        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = _sample_property_schema()
        mock_get_agent_type.return_value = mock_agent_type

        handle_edit_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        self.client.views_open.assert_called_once()
        call_kwargs = self.client.views_open.call_args[1]
        assert call_kwargs["trigger_id"] == "trigger_123"
        assert call_kwargs["view"]["callback_id"] == "correction_modal_submit"

    def test_no_session_acks_and_posts_guidance(self):
        # No state set for U1
        handle_edit_action(
            ack=self.ack,
            body=_body("U1", "D000"),
            state_manager=self.sm,
            client=self.client,
        )

        self.ack.assert_called_once()
        self.client.chat_postMessage.assert_called_once()
        call_kwargs = self.client.chat_postMessage.call_args[1]
        assert "/create-character" in call_kwargs["text"]


# ---------------------------------------------------------------------------
# Tests: handle_correction_modal_submit (AC-25)
# ---------------------------------------------------------------------------


class TestHandleCorrectionModalSubmit:
    """Test the correction modal submission handler."""

    def setup_method(self):
        self.sm = StateManager()
        self.ack = MagicMock()
        self.client = MagicMock()

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_updates_all_freeform_fields(self, mock_get_agent_type):
        state = _complete_state()
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(
                name="New Name",
                description="New desc",
                motivations="New motivations",
                backstory="New backstory",
                relationships="New relationships",
            ),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").name == "New Name"
        assert self.sm.get("U1").description == "New desc"
        assert self.sm.get("U1").motivations == "New motivations"
        assert self.sm.get("U1").backstory == "New backstory"
        assert self.sm.get("U1").relationships == "New relationships"

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_updates_role(self, mock_get_agent_type):
        state = _complete_state()
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(role="antagonist"),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").role == "antagonist"

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_updates_agent_config_enabled(self, mock_get_agent_type):
        state = _complete_state()
        state.agent_config_enabled = False
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(toggle_on=True),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").agent_config_enabled is True

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_updates_agent_properties_when_enabled(self, mock_get_agent_type):
        state = _complete_state()
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(toggle_on=True, prop_a="90", prop_b="85"),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").agent_properties == {"prop_a": 90.0, "prop_b": 85.0}

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_clears_agent_config_when_disabled(self, mock_get_agent_type):
        state = _complete_state()
        state.agent_config_enabled = True
        state.agent_properties = {"prop_a": 75.0}
        state.agent_instructions = "Old instructions"
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(toggle_on=False),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        assert self.sm.get("U1").agent_config_enabled is False
        assert self.sm.get("U1").agent_properties == {}
        assert self.sm.get("U1").agent_instructions == ""

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_validates_property_range(self, mock_get_agent_type):
        state = _complete_state()
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(toggle_on=True, prop_a="150"),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        # Should ack with errors
        self.ack.assert_called_once()
        call_args = self.ack.call_args
        assert "errors" in call_args[1]
        assert "prop_a_block" in call_args[1]["errors"]

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_phase_remains_preview(self, mock_get_agent_type):
        state = _complete_state()
        state.phase = WizardPhase.PREVIEW
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        # Phase should remain PREVIEW (AC-25)
        assert self.sm.get("U1").phase == WizardPhase.PREVIEW

    @patch("slack_app.handlers.submissions.get_character_agent_type")
    def test_posts_updated_preview(self, mock_get_agent_type):
        state = _complete_state()
        self.sm.set("U1", state)

        mock_agent_type = MagicMock()
        mock_agent_type.property_schema = {"properties": {"prop_a": {}, "prop_b": {}}}
        mock_get_agent_type.return_value = mock_agent_type

        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(name="Updated Name"),
            body=_body("U1"),
            state_manager=self.sm,
            client=self.client,
        )

        self.client.chat_postMessage.assert_called_once()
        call_kwargs = self.client.chat_postMessage.call_args[1]
        assert call_kwargs["channel"] == "D000"
        # Should contain preview message structure
        assert "blocks" in call_kwargs

    def test_no_session_acks_without_error(self):
        handle_correction_modal_submit(
            ack=self.ack,
            view=_correction_view(),
            body=_body("U_UNKNOWN"),
            state_manager=self.sm,
            client=self.client,
        )

        self.ack.assert_called_once()
        self.client.chat_postMessage.assert_not_called()
