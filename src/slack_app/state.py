"""Wizard state machine for the Slack character creation flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from models import CharacterAgentConfig, CharacterProfile


class WizardPhase(Enum):
    WAITING_NAME = auto()
    WAITING_DESCRIPTION = auto()
    WAITING_MOTIVATIONS = auto()
    WAITING_BACKSTORY = auto()
    WAITING_RELATIONSHIPS = auto()
    MODAL_1_OPEN = auto()
    MODAL_2_OPEN = auto()
    PREVIEW = auto()
    SAVED = auto()


@dataclass
class WizardState:
    """Per-user state carried through the character creation wizard."""

    phase: WizardPhase
    name: str = ""
    description: str = ""
    motivations: str = ""
    backstory: str = ""
    relationships: str = ""
    role: str = "supporting"
    agent_config_enabled: bool = False
    agent_type: str = "default"
    agent_properties: dict[str, Any] = field(default_factory=dict)
    agent_instructions: str = ""

    def to_character_profile(self) -> CharacterProfile:
        """Assemble a CharacterProfile from the collected wizard state."""
        agent_config = None
        if self.agent_config_enabled:
            agent_config = CharacterAgentConfig(
                agent_type=self.agent_type,
                agent_properties=self.agent_properties,
                agent_instructions=self.agent_instructions,
            )

        return CharacterProfile(
            name=self.name,
            description=self.description,
            role=self.role,
            motivations=self.motivations,
            relationships=self.relationships,
            backstory=self.backstory,
            agent_config=agent_config,
        )
