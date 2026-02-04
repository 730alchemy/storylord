from typing import Any

from pydantic import BaseModel, Field


class MemoryEvent(BaseModel):
    """A single event in character memory."""

    event_type: str  # spoke, thought, chose, heard, witnessed
    content: str
    scene_reference: str = ""
    other_characters: list[str] = []


class EmotionalSnapshot(BaseModel):
    """A point-in-time capture of emotional state."""

    state: str
    trigger: str = ""
    scene_reference: str = ""


class KnowledgeItem(BaseModel):
    """Something the character has learned."""

    fact: str
    source: str = ""  # how they learned it
    confidence: float = 1.0


class RelationshipState(BaseModel):
    """Current state of a relationship with another character."""

    character_name: str
    sentiment: str = "neutral"  # positive, negative, neutral, conflicted
    trust_level: float = 0.5  # 0.0 to 1.0
    notes: list[str] = []


class CharacterMemory(BaseModel):
    """Persistent memory for a character across scenes."""

    events: list[MemoryEvent] = []
    emotional_arc: list[EmotionalSnapshot] = []
    knowledge: list[KnowledgeItem] = []
    relationships: dict[str, RelationshipState] = {}
    current_emotional_state: str = "neutral"

    def add_interaction(
        self,
        event_type: str,
        content: str,
        scene_reference: str = "",
        other_characters: list[str] | None = None,
        emotional_state: str | None = None,
    ) -> None:
        """Record an interaction in memory.

        Args:
            event_type: Type of event (spoke, thought, chose, etc.).
            content: What happened.
            scene_reference: Reference to the scene.
            other_characters: Other characters involved.
            emotional_state: Optional emotional state change.
        """
        self.events.append(
            MemoryEvent(
                event_type=event_type,
                content=content,
                scene_reference=scene_reference,
                other_characters=other_characters or [],
            )
        )
        if emotional_state:
            self.current_emotional_state = emotional_state
            self.emotional_arc.append(
                EmotionalSnapshot(
                    state=emotional_state,
                    trigger=content[:100],
                    scene_reference=scene_reference,
                )
            )

    def add_knowledge(
        self,
        fact: str,
        source: str = "",
        confidence: float = 1.0,
    ) -> None:
        """Add a piece of knowledge to memory.

        Args:
            fact: The knowledge item.
            source: How the character learned this.
            confidence: How certain the character is.
        """
        self.knowledge.append(
            KnowledgeItem(fact=fact, source=source, confidence=confidence)
        )

    def update_relationship(
        self,
        character_name: str,
        sentiment: str | None = None,
        trust_delta: float = 0.0,
        note: str | None = None,
    ) -> None:
        """Update relationship state with another character.

        Args:
            character_name: The other character's name.
            sentiment: New sentiment value if changing.
            trust_delta: Change in trust level (-1.0 to 1.0).
            note: Optional note to add about the relationship.
        """
        if character_name not in self.relationships:
            self.relationships[character_name] = RelationshipState(
                character_name=character_name
            )

        rel = self.relationships[character_name]
        if sentiment:
            rel.sentiment = sentiment
        rel.trust_level = max(0.0, min(1.0, rel.trust_level + trust_delta))
        if note:
            rel.notes.append(note)

    def get_summary(self, max_events: int = 5) -> str:
        """Get a summary of recent memory for context.

        Args:
            max_events: Maximum number of recent events to include.

        Returns:
            A text summary of recent memory.
        """
        lines = []
        if self.events:
            recent = self.events[-max_events:]
            lines.append("Recent events:")
            for event in recent:
                lines.append(f"  - [{event.event_type}] {event.content[:80]}...")

        if self.knowledge:
            lines.append(f"Known facts: {len(self.knowledge)} items")

        if self.relationships:
            rel_summary = ", ".join(
                f"{k}: {v.sentiment}" for k, v in self.relationships.items()
            )
            lines.append(f"Relationships: {rel_summary}")

        lines.append(f"Current emotional state: {self.current_emotional_state}")

        return "\n".join(lines) if lines else "No significant memories yet."

    def get_emotional_arc(self) -> str:
        """Get a summary of the character's emotional journey.

        Returns:
            A text description of the emotional arc.
        """
        if not self.emotional_arc:
            return "Emotional state has remained stable."

        states = [snap.state for snap in self.emotional_arc[-5:]]
        return f"Recent emotional states: {' -> '.join(states)}"


class CharacterAgentConfig(BaseModel):
    """Agent configuration for a character."""

    agent_type: str = "default"
    agent_properties: dict[str, Any] = Field(default_factory=dict)
    agent_instructions: str = ""


class CharacterProfile(BaseModel):
    """A character in the story with their profile details."""

    name: str
    description: str
    role: str  # protagonist, antagonist, supporting, etc.
    motivations: str
    relationships: str  # relationships to other characters
    backstory: str
    agent_config: CharacterAgentConfig | None = None


class ArchitectInput(BaseModel):
    """Input parameters for the architect agent."""

    story_idea: str
    characters: list[CharacterProfile]
    num_plot_events: int
    beats_per_event: tuple[int, int]  # (min, max) range
    tone: str


class StoryInput(BaseModel):
    """Input for the complete story generation pipeline."""

    story_idea: str
    characters: list[CharacterProfile]
    num_plot_events: int
    beats_per_event: tuple[int, int]  # (min, max) range
    tone: str
    output_file: str

    # Characters from the persistent library (resolved at load time)
    character_library: list[str] = Field(default_factory=list)

    # Agent and tool selection (discovered via entry points)
    architect: str = "default"
    narrator: str = "default"
    tools: list[str] | None = None


class StoryBeat(BaseModel):
    """A narrative event within a plot event."""

    description: str
    beat_type: str  # conversation, action, occurrence, internal_dialogue, etc.
    characters_involved: list[str]


class PlotEvent(BaseModel):
    """A major plot point containing story beats."""

    title: str
    summary: str
    beats: list[StoryBeat]


class StoryArchitecture(BaseModel):
    """Complete story structure with all plot events and their beats."""

    plot_events: list[PlotEvent]


# Narrator agent models


class NarratorInput(BaseModel):
    """Input parameters for the narrator agent."""

    story_architecture: StoryArchitecture
    characters: list[CharacterProfile]
    tone: str
    run_id: str | None = None


class BeatNarration(BaseModel):
    """Narrative text for a single story beat."""

    narrative_text: str
    beat_reference: str  # e.g., "Event 1, Beat 2"


class ConflictEvaluation(BaseModel):
    """Result of evaluating narrative against the story corpus."""

    conflicts_found: list[str]
    revised_narrative: str


class NarratedStory(BaseModel):
    """Complete narrated story output."""

    narrations: list[BeatNarration]


# Editor agent models


class EditorInput(BaseModel):
    """Input parameters for the editor agent."""

    text: str


class EditedText(BaseModel):
    """Output from the editor agent."""

    text: str
