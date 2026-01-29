"""Tests for tools/context.py."""

from __future__ import annotations

from tools.context import ToolExecutionContext


class TestToolExecutionContext:
    """Tests for ToolExecutionContext dataclass."""

    def test_default_values(self):
        """Context should have None defaults for all fields."""
        context = ToolExecutionContext()
        assert context.character_registry is None
        assert context.run_id is None
        assert context.trace_id is None
        assert context.beat_reference is None

    def test_with_all_fields(self):
        """Context should accept all fields."""
        context = ToolExecutionContext(
            character_registry="fake_registry",  # type: ignore
            run_id="run-123",
            trace_id="trace-456",
            beat_reference="Event 1, Beat 2",
        )
        assert context.character_registry == "fake_registry"
        assert context.run_id == "run-123"
        assert context.trace_id == "trace-456"
        assert context.beat_reference == "Event 1, Beat 2"

    def test_partial_fields(self):
        """Context should allow partial field specification."""
        context = ToolExecutionContext(run_id="run-only")
        assert context.run_id == "run-only"
        assert context.trace_id is None

    def test_equality(self):
        """Contexts with same values should be equal."""
        ctx1 = ToolExecutionContext(run_id="run-1", trace_id="trace-1")
        ctx2 = ToolExecutionContext(run_id="run-1", trace_id="trace-1")
        assert ctx1 == ctx2

    def test_inequality(self):
        """Contexts with different values should not be equal."""
        ctx1 = ToolExecutionContext(run_id="run-1")
        ctx2 = ToolExecutionContext(run_id="run-2")
        assert ctx1 != ctx2
