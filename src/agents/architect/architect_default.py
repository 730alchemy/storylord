"""Default architect implementation for storylord."""

from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from config import get_model_for_agent_type
from models import ArchitectInput, PlotEvent, StoryArchitecture
from tools.registry import ToolRegistry

log = structlog.get_logger(__name__)


SYSTEM_PROMPT = """You are a master story architect. Your task is to create compelling plot events \
with detailed story beats that build a cohesive narrative.

A story beat is a narrative event essential to developing a plot event. Beat types include:
- conversation: Dialogue between characters
- action: Physical actions or events
- occurrence: External events that affect the story
- internal_dialogue: A character's inner thoughts
- revelation: Information revealed to characters or readers
- decision: A character making a significant choice

When creating plot events and beats:
- Ensure each beat advances the story meaningfully
- Create natural progressions between beats
- Use character motivations and relationships to drive conflict
- Maintain the specified tone throughout
- Build on previous plot events for narrative continuity"""


USER_PROMPT_TEMPLATE = """## Story Context

**Story Idea:** {story_idea}

**Tone:** {tone}

**Characters:**
{characters_text}

## Current Task

Generate plot event {current_event} of {total_events}.

Create between {min_beats} and {max_beats} story beats for this plot event.

{previous_events_section}

Create a plot event that naturally follows from the story so far (or begins the story if this is the first event). \
Ensure beats flow logically and advance the narrative."""


class DefaultArchitect:
    """Default architect implementation using Claude Sonnet.

    This architect generates story structures iteratively, building each plot event
    with context from previous events to maintain narrative continuity.
    """

    name = "default"

    def generate(
        self,
        input: ArchitectInput,
        tools: ToolRegistry | None = None,
    ) -> StoryArchitecture:
        """Generate a complete story architecture with plot events and beats.

        Args:
            input: The architect input parameters.
            tools: Optional tool registry (not used by default architect).

        Returns:
            A complete story architecture.
        """
        chain = self._create_chain()
        plot_events: list[PlotEvent] = []
        characters_text = self._format_characters(input.characters)
        min_beats, max_beats = input.beats_per_event

        for i in range(input.num_plot_events):
            current_event = i + 1
            previous_events_section = self._format_previous_events(plot_events)

            result = chain.invoke(
                {
                    "story_idea": input.story_idea,
                    "tone": input.tone,
                    "characters_text": characters_text,
                    "current_event": current_event,
                    "total_events": input.num_plot_events,
                    "min_beats": min_beats,
                    "max_beats": max_beats,
                    "previous_events_section": previous_events_section,
                }
            )

            log.info(
                "plot_event_complete",
                architect=self.name,
                plot_event=current_event,
                total_events=input.num_plot_events,
                beats=len(result.beats),
            )
            plot_events.append(result)

        return StoryArchitecture(plot_events=plot_events)

    def _create_chain(self):
        """Create the LangChain chain for generating plot events."""
        llm = ChatAnthropic(model=get_model_for_agent_type("architect"))
        structured_llm = llm.with_structured_output(PlotEvent)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT_TEMPLATE),
            ]
        )

        return prompt | structured_llm

    def _format_characters(self, characters: list) -> str:
        """Format character profiles for the prompt."""
        lines = []
        for char in characters:
            lines.append(f"### {char.name} ({char.role})")
            lines.append(f"**Description:** {char.description}")
            lines.append(f"**Motivations:** {char.motivations}")
            lines.append(f"**Relationships:** {char.relationships}")
            lines.append(f"**Backstory:** {char.backstory}")
            lines.append("")
        return "\n".join(lines)

    def _format_previous_events(self, events: list[PlotEvent]) -> str:
        """Format previously generated plot events for context."""
        if not events:
            return "**Previous Plot Events:** None (this is the first event)"

        lines = ["**Previous Plot Events:**\n"]
        for i, event in enumerate(events, 1):
            lines.append(f"### Event {i}: {event.title}")
            lines.append(f"{event.summary}")
            lines.append("\nBeats:")
            for beat in event.beats:
                chars = (
                    ", ".join(beat.characters_involved)
                    if beat.characters_involved
                    else "None"
                )
                lines.append(
                    f"- [{beat.beat_type}] {beat.description} (Characters: {chars})"
                )
            lines.append("")
        return "\n".join(lines)
