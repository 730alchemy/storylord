"""DM message handler for freeform field collection in the character wizard."""

from __future__ import annotations

from typing import Callable

import structlog

from slack_app.state import StateManager, WizardPhase

log = structlog.get_logger(__name__)

# Ordered sequence of freeform phases and the field each populates.
_FREEFORM_STEPS: list[tuple[WizardPhase, str]] = [
    (WizardPhase.WAITING_NAME, "name"),
    (WizardPhase.WAITING_DESCRIPTION, "description"),
    (WizardPhase.WAITING_MOTIVATIONS, "motivations"),
    (WizardPhase.WAITING_BACKSTORY, "backstory"),
    (WizardPhase.WAITING_RELATIONSHIPS, "relationships"),
]

# Prompt sent after a field is captured, keyed by the phase just entered.
_NEXT_PROMPT: dict[WizardPhase, str] = {
    WizardPhase.WAITING_DESCRIPTION: "Nice! Now describe {name} — a sentence or two is fine.",
    WizardPhase.WAITING_MOTIVATIONS: "What drives {name}? What are their motivations?",
    WizardPhase.WAITING_BACKSTORY: "Tell me about {name}'s backstory.",
    WizardPhase.WAITING_RELATIONSHIPS: 'How does {name} relate to other characters? (type "skip" to leave this blank)',
}

# Guidance text shown when a user sends an invalid or unexpected message.
_PHASE_GUIDANCE: dict[WizardPhase, str] = {
    WizardPhase.WAITING_NAME: "Please type the character's name.",
    WizardPhase.WAITING_DESCRIPTION: "Please type a description for the character.",
    WizardPhase.WAITING_MOTIVATIONS: "Please type the character's motivations.",
    WizardPhase.WAITING_BACKSTORY: "Please type the character's backstory.",
    WizardPhase.WAITING_RELATIONSHIPS: 'Please type the character\'s relationships, or "skip" to leave blank.',
    WizardPhase.MODAL_1_OPEN: "Please fill out the form that's open.",
    WizardPhase.MODAL_2_OPEN: "Please fill out the form that's open.",
    WizardPhase.PREVIEW: "Please use the Save or Edit buttons in the preview message.",
}


def handle_message(
    message: dict,
    say: Callable,
    state_manager: StateManager,
) -> None:
    """Handle an incoming DM during the character creation wizard.

    Routes based on the user's current wizard phase. Non-DM messages
    and messages with subtypes (bot messages, joins, etc.) are silently
    ignored. Users without an active session or in a non-text phase
    receive guidance.
    """
    if message.get("channel_type") != "im":
        log.info("message_ignored_not_im", channel_type=message.get("channel_type"))
        return
    if message.get("subtype"):
        log.info("message_ignored_subtype", subtype=message.get("subtype"))
        return

    user_id = message["user"]
    state = state_manager.get(user_id)

    if state is None:
        log.info("message_no_active_session", user=user_id)
        say(text="No character creation in progress. Use `/create-character` to start.")
        return

    text = (message.get("text") or "").strip()
    log.info("message_processing", user=user_id, phase=state.phase.name, text=text[:80])

    # No usable text (e.g. image or file with no caption) — AC-29
    if not text:
        say(text=_guidance_for_phase(state.phase))
        return

    # Not in a freeform phase — guide the user (AC-29)
    step_index = _find_step_index(state.phase)
    if step_index is None:
        say(text=_guidance_for_phase(state.phase))
        return

    phase, field_name = _FREEFORM_STEPS[step_index]

    # Relationships: "skip" (case-insensitive) → empty string — AC-12
    if phase == WizardPhase.WAITING_RELATIONSHIPS and text.lower() == "skip":
        setattr(state, field_name, "")
    else:
        setattr(state, field_name, text)

    # Advance to the next phase
    next_index = step_index + 1
    if next_index < len(_FREEFORM_STEPS):
        next_phase, _ = _FREEFORM_STEPS[next_index]
        state.phase = next_phase
        log.info(
            "message_field_captured",
            user=user_id,
            field=field_name,
            next_phase=next_phase.name,
        )
        say(text=_NEXT_PROMPT[next_phase].format(name=state.name))
    else:
        # Past the last freeform phase — hand off to Modal 1 (Slice 5)
        state.phase = WizardPhase.MODAL_1_OPEN
        log.info(
            "message_field_captured",
            user=user_id,
            field=field_name,
            next_phase="MODAL_1_OPEN",
        )
        say(
            text="Great! Now let's set their role and personality. Opening a quick form..."
        )


def _find_step_index(phase: WizardPhase) -> int | None:
    """Return the index into _FREEFORM_STEPS for *phase*, or None."""
    for i, (p, _) in enumerate(_FREEFORM_STEPS):
        if p == phase:
            return i
    return None


def _guidance_for_phase(phase: WizardPhase) -> str:
    """Return guidance text appropriate for the given phase."""
    return _PHASE_GUIDANCE.get(
        phase, "Use `/create-character` to start a new character."
    )
