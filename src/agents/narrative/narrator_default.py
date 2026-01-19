"""Default narrator implementation for storylord."""

from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from agents.character.registry import CharacterRegistry
from models import (
    BeatNarration,
    CharacterProfile,
    ConflictEvaluation,
    NarratedStory,
    NarratorInput,
    PlotEvent,
    StoryBeat,
)
from tools.registry import ToolRegistry

log = structlog.get_logger(__name__)


GENERATION_SYSTEM_PROMPT = """You are a master storyteller and narrator. Your task is to transform story beats \
into vivid, engaging narrative prose.

When writing narrative:
- Match the specified tone throughout your prose
- Write dialogue that reflects each character's personality and motivations
- Show rather than tell - use sensory details and action
- Maintain consistent point of view
- Create smooth transitions that flow naturally from previous narrative
- Bring the story beat to life while staying true to its description

You must generate narrative text that fulfills the story beat's requirements while maintaining \
consistency with everything that has come before in the story."""


GENERATION_USER_TEMPLATE = """## Current Plot Event

**Title:** {event_title}
**Summary:** {event_summary}

## Story Beat to Develop

**Beat Type:** {beat_type}
**Description:** {beat_description}

## Characters in This Beat

{involved_characters}

## Tone

{tone}

## Prior Story Context

{prior_context}

## Narrative Written So Far

{prior_narration}

---

Write the narrative prose for this story beat. The narrative should naturally continue from \
what has been written so far (or begin the story if this is the first beat). Include dialogue \
where appropriate for the characters involved."""


EVALUATION_SYSTEM_PROMPT = """You are a meticulous continuity editor. Your task is to evaluate narrative text \
against the full story corpus and identify any conflicts or inconsistencies.

Look for these types of conflicts:
- Timeline inconsistencies (events happening out of order, contradictory timing)
- Character behavior inconsistencies (acting against established personality or motivations)
- Factual inconsistencies (contradicting previously established facts)
- Dialogue inconsistencies (characters knowing things they shouldn't, forgetting things they should know)
- Setting inconsistencies (contradicting established locations or environments)
- Tone inconsistencies (jarring shifts that don't match the story's established feel)

After identifying conflicts, revise the narrative to resolve them while preserving the core \
content and advancing the story beat. If no conflicts are found, return the narrative unchanged."""


EVALUATION_USER_TEMPLATE = """## Current Narrative to Evaluate

{current_narrative}

## Story Beat Being Narrated

**Beat Type:** {beat_type}
**Description:** {beat_description}

## Full Story Corpus (All Previous Narrative)

{full_corpus}

## Prior Plot Events and Beats

{prior_context}

---

Evaluate the current narrative against the full story corpus. Identify any conflicts or \
inconsistencies, then provide a revised version that resolves them. If no conflicts exist, \
return the narrative as-is."""


class DefaultNarrator:
    """Default narrator implementation using Claude Sonnet.

    This narrator transforms story beats into narrative prose through an iterative
    process of generation and evaluation to ensure consistency.
    """

    name = "default"

    def generate(
        self,
        input: NarratorInput,
        tools: ToolRegistry | None = None,
        character_registry: CharacterRegistry | None = None,
    ) -> NarratedStory:
        """Generate complete narrative prose from a story architecture.

        Processes each story beat sequentially with three iterations:
        1. Generate initial narrative text
        2. Evaluate against corpus and revise
        3. Evaluate again and revise

        Args:
            input: The narrator input parameters.
            tools: Optional tool registry (not used by default narrator).
            character_registry: Optional registry of character agent instances.

        Returns:
            A complete narrated story.
        """
        self._character_registry = character_registry
        generation_chain = self._create_generation_chain()
        evaluation_chain = self._create_evaluation_chain()

        all_narrations: list[BeatNarration] = []
        plot_events = input.story_architecture.plot_events

        for event_idx, plot_event in enumerate(plot_events):
            prior_events = plot_events[:event_idx]
            event_title, event_summary = self._format_current_plot_event(plot_event)

            for beat_idx, beat in enumerate(plot_event.beats):
                beat_type, beat_description = self._format_story_beat(beat)
                beat_reference = f"Event {event_idx + 1}, Beat {beat_idx + 1}"

                # Build context for generation
                generation_context = {
                    "event_title": event_title,
                    "event_summary": event_summary,
                    "beat_type": beat_type,
                    "beat_description": beat_description,
                    "involved_characters": self._format_involved_characters(
                        beat, input.characters
                    ),
                    "tone": input.tone,
                    "prior_context": self._format_prior_context(
                        prior_events, plot_event, beat_idx
                    ),
                    "prior_narration": self._format_prior_narration(all_narrations),
                }

                # Iteration 1: Generate initial narrative
                narration = generation_chain.invoke(generation_context)
                narration.beat_reference = beat_reference
                log.info(
                    "beat_iteration_complete",
                    narrator=self.name,
                    plot_event=event_idx + 1,
                    beat=beat_idx + 1,
                    iteration=1,
                    phase="generate",
                )

                # Iterations 2 and 3: Evaluate and revise
                for iteration in range(2, 4):
                    eval_context = {
                        "current_narrative": narration.narrative_text,
                        "beat_type": beat_type,
                        "beat_description": beat_description,
                        "full_corpus": self._format_prior_narration(all_narrations),
                        "prior_context": self._format_prior_context(
                            prior_events, plot_event, beat_idx
                        ),
                    }

                    eval_result = evaluation_chain.invoke(eval_context)

                    if eval_result.conflicts_found:
                        log.info(
                            "conflicts_found",
                            narrator=self.name,
                            plot_event=event_idx + 1,
                            beat=beat_idx + 1,
                            iteration=iteration,
                            conflicts=eval_result.conflicts_found,
                        )
                    else:
                        log.info(
                            "no_conflicts_found",
                            narrator=self.name,
                            plot_event=event_idx + 1,
                            beat=beat_idx + 1,
                            iteration=iteration,
                        )

                    narration.narrative_text = eval_result.revised_narrative
                    log.info(
                        "beat_iteration_complete",
                        narrator=self.name,
                        plot_event=event_idx + 1,
                        beat=beat_idx + 1,
                        iteration=iteration,
                        phase="evaluate",
                    )

                    # Exit early if first evaluation finds no conflicts
                    if not eval_result.conflicts_found:
                        break

                all_narrations.append(narration)

        return NarratedStory(narrations=all_narrations)

    def _create_generation_chain(self):
        """Create the LangChain chain for generating narrative prose."""
        llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        structured_llm = llm.with_structured_output(BeatNarration)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", GENERATION_SYSTEM_PROMPT),
                ("user", GENERATION_USER_TEMPLATE),
            ]
        )

        return prompt | structured_llm

    def _create_evaluation_chain(self):
        """Create the LangChain chain for evaluating and revising narrative."""
        llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        structured_llm = llm.with_structured_output(ConflictEvaluation)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EVALUATION_SYSTEM_PROMPT),
                ("user", EVALUATION_USER_TEMPLATE),
            ]
        )

        return prompt | structured_llm

    def _format_current_plot_event(self, event: PlotEvent) -> tuple[str, str]:
        """Format the current plot event title and summary."""
        return event.title, event.summary

    def _format_story_beat(self, beat: StoryBeat) -> tuple[str, str]:
        """Format the story beat type and description."""
        return beat.beat_type, beat.description

    def _format_involved_characters(
        self, beat: StoryBeat, characters: list[CharacterProfile]
    ) -> str:
        """Format character profiles for characters involved in this beat."""
        involved_names = set(beat.characters_involved)
        involved_chars = [c for c in characters if c.name in involved_names]

        if not involved_chars:
            return "No specific characters identified for this beat."

        lines = []
        for char in involved_chars:
            lines.append(f"### {char.name} ({char.role})")
            lines.append(f"**Description:** {char.description}")
            lines.append(f"**Motivations:** {char.motivations}")
            lines.append(f"**Relationships:** {char.relationships}")
            lines.append("")
        return "\n".join(lines)

    def _format_prior_context(
        self,
        prior_events: list[PlotEvent],
        current_event: PlotEvent,
        current_beat_idx: int,
    ) -> str:
        """Format all prior plot events and beats for context."""
        if not prior_events and current_beat_idx == 0:
            return "This is the beginning of the story. No prior context."

        lines = []

        # Previous plot events
        for i, event in enumerate(prior_events, 1):
            lines.append(f"### Plot Event {i}: {event.title}")
            lines.append(f"{event.summary}\n")
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

        # Earlier beats from current event
        if current_beat_idx > 0:
            event_num = len(prior_events) + 1
            lines.append(f"### Plot Event {event_num} (Current): {current_event.title}")
            lines.append(f"{current_event.summary}\n")
            for beat in current_event.beats[:current_beat_idx]:
                chars = (
                    ", ".join(beat.characters_involved)
                    if beat.characters_involved
                    else "None"
                )
                lines.append(
                    f"- [{beat.beat_type}] {beat.description} (Characters: {chars})"
                )
            lines.append("")

        return "\n".join(lines) if lines else "No prior context."

    def _format_prior_narration(self, narrations: list[BeatNarration]) -> str:
        """Format all previously written narrative text."""
        if not narrations:
            return "No narrative has been written yet. This is the first beat."

        lines = []
        for narration in narrations:
            lines.append(f"--- {narration.beat_reference} ---")
            lines.append(narration.narrative_text)
            lines.append("")
        return "\n".join(lines)
