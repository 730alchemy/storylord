"""Runtime context for tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.character.registry import CharacterRegistry


@dataclass(slots=True)
class ToolExecutionContext:
    """Context passed to tools during execution."""

    character_registry: "CharacterRegistry | None" = None
    run_id: str | None = None
    trace_id: str | None = None
    beat_reference: str | None = None
