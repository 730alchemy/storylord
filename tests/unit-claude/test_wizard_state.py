"""Unit tests for WizardPhase and WizardState."""

from __future__ import annotations

from slack_app.state import WizardPhase, WizardState


class TestWizardPhase:
    """Tests for the WizardPhase enum."""

    def test_given_all_phases_defined_when_inspected_then_matches_state_machine_in_spec(
        self,
    ):
        """All phases from the spec's state machine are present."""
        expected = {
            "WAITING_NAME",
            "WAITING_DESCRIPTION",
            "WAITING_MOTIVATIONS",
            "WAITING_BACKSTORY",
            "WAITING_RELATIONSHIPS",
            "MODAL_1_OPEN",
            "MODAL_2_OPEN",
            "PREVIEW",
            "SAVED",
        }
        assert {phase.name for phase in WizardPhase} == expected


class TestWizardStateToCharacterProfile:
    """Tests for WizardState.to_character_profile()."""

    def test_given_wizard_state_with_all_freeform_fields_and_no_agent_config_when_to_character_profile_called_then_agent_config_is_None(
        self,
    ):
        """Profile has no agent_config when the wizard toggle was off."""
        state = WizardState(
            phase=WizardPhase.PREVIEW,
            name="Elijah Boondog",
            description="A dentist",
            role="protagonist",
            motivations="Curiosity",
            backstory="Lost in thought",
            relationships="Best friends with Jasper",
            agent_config_enabled=False,
        )

        profile = state.to_character_profile()

        assert profile.name == "Elijah Boondog"
        assert profile.description == "A dentist"
        assert profile.role == "protagonist"
        assert profile.motivations == "Curiosity"
        assert profile.backstory == "Lost in thought"
        assert profile.relationships == "Best friends with Jasper"
        assert profile.agent_config is None

    def test_given_wizard_state_with_agent_config_enabled_when_to_character_profile_called_then_agent_config_is_populated(
        self,
    ):
        """Profile has a fully populated agent_config when the wizard toggle was on."""
        state = WizardState(
            phase=WizardPhase.PREVIEW,
            name="Jasper Dilsack",
            description="A lawyer",
            role="protagonist",
            motivations="Winning",
            backstory="Skipped grades",
            relationships="",
            agent_config_enabled=True,
            agent_type="mbti",
            agent_properties={
                "extroversion": 90,
                "intuition": 7,
                "thinking": 1,
                "judging": 99,
            },
            agent_instructions="use a lot of gen z slang",
        )

        profile = state.to_character_profile()

        assert profile.agent_config is not None
        assert profile.agent_config.agent_type == "mbti"
        assert profile.agent_config.agent_properties["extroversion"] == 90
        assert profile.agent_config.agent_instructions == "use a lot of gen z slang"

    def test_given_wizard_state_with_default_values_when_to_character_profile_called_then_required_fields_present(
        self,
    ):
        """A state with only the minimum populated still produces a valid CharacterProfile."""
        state = WizardState(
            phase=WizardPhase.PREVIEW,
            name="Someone",
            description="Someone",
            role="supporting",
            motivations="Something",
            backstory="Nothing",
        )

        profile = state.to_character_profile()

        assert profile.name == "Someone"
        assert profile.role == "supporting"
        assert profile.agent_config is None
