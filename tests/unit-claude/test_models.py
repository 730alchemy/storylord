"""Unit tests for CharacterMemory class in models.py."""

import pytest

from models import CharacterMemory


class TestCharacterMemoryAddInteraction:
    """Tests for CharacterMemory.add_interaction()."""

    def test_add_interaction_basic(self, empty_memory: CharacterMemory):
        """Basic interaction is recorded in events list."""
        empty_memory.add_interaction(
            event_type="spoke",
            content="Hello, world!",
            scene_reference="scene_1",
        )

        assert len(empty_memory.events) == 1
        assert empty_memory.events[0].event_type == "spoke"
        assert empty_memory.events[0].content == "Hello, world!"
        assert empty_memory.events[0].scene_reference == "scene_1"
        assert empty_memory.events[0].other_characters == []

    def test_add_interaction_with_other_characters(self, empty_memory: CharacterMemory):
        """Interaction records other characters involved."""
        empty_memory.add_interaction(
            event_type="spoke",
            content="Talking to friends",
            other_characters=["Alice", "Bob"],
        )

        assert empty_memory.events[0].other_characters == ["Alice", "Bob"]

    def test_add_interaction_none_other_characters_becomes_empty_list(
        self, empty_memory: CharacterMemory
    ):
        """When other_characters is None, it becomes an empty list."""
        empty_memory.add_interaction(
            event_type="witnessed",
            content="Something happened",
            other_characters=None,
        )

        assert empty_memory.events[0].other_characters == []

    def test_add_interaction_with_emotional_state(self, empty_memory: CharacterMemory):
        """Emotional state updates arc and current state."""
        empty_memory.add_interaction(
            event_type="witnessed",
            content="Saw a tragedy",
            emotional_state="sad",
        )

        assert empty_memory.current_emotional_state == "sad"
        assert len(empty_memory.emotional_arc) == 1
        assert empty_memory.emotional_arc[0].state == "sad"
        assert empty_memory.emotional_arc[0].trigger == "Saw a tragedy"

    def test_add_interaction_without_emotional_state(
        self, empty_memory: CharacterMemory
    ):
        """When no emotional state provided, emotional arc is not updated."""
        empty_memory.add_interaction(
            event_type="spoke",
            content="Just talking",
        )

        assert empty_memory.current_emotional_state == "neutral"  # Default
        assert len(empty_memory.emotional_arc) == 0

    def test_add_interaction_truncates_trigger_at_100_chars(
        self, empty_memory: CharacterMemory
    ):
        """Content longer than 100 chars is truncated in trigger."""
        long_content = "x" * 150
        empty_memory.add_interaction(
            event_type="spoke",
            content=long_content,
            emotional_state="excited",
        )

        assert len(empty_memory.emotional_arc[0].trigger) == 100
        assert empty_memory.emotional_arc[0].trigger == "x" * 100

    def test_add_interaction_preserves_full_content_in_event(
        self, empty_memory: CharacterMemory
    ):
        """Full content is preserved in event even when trigger is truncated."""
        long_content = "x" * 150
        empty_memory.add_interaction(
            event_type="spoke",
            content=long_content,
            emotional_state="excited",
        )

        assert len(empty_memory.events[0].content) == 150

    def test_add_multiple_interactions(self, empty_memory: CharacterMemory):
        """Multiple interactions are recorded in order."""
        empty_memory.add_interaction(event_type="spoke", content="First")
        empty_memory.add_interaction(event_type="thought", content="Second")
        empty_memory.add_interaction(event_type="chose", content="Third")

        assert len(empty_memory.events) == 3
        assert empty_memory.events[0].content == "First"
        assert empty_memory.events[1].content == "Second"
        assert empty_memory.events[2].content == "Third"


class TestCharacterMemoryAddKnowledge:
    """Tests for CharacterMemory.add_knowledge()."""

    def test_add_knowledge_basic(self, empty_memory: CharacterMemory):
        """Basic knowledge item is added with defaults."""
        empty_memory.add_knowledge(fact="The sky is blue")

        assert len(empty_memory.knowledge) == 1
        assert empty_memory.knowledge[0].fact == "The sky is blue"
        assert empty_memory.knowledge[0].source == ""
        assert empty_memory.knowledge[0].confidence == 1.0

    def test_add_knowledge_with_source(self, empty_memory: CharacterMemory):
        """Knowledge with source is recorded correctly."""
        empty_memory.add_knowledge(
            fact="Water boils at 100C",
            source="science class",
        )

        assert empty_memory.knowledge[0].source == "science class"

    @pytest.mark.parametrize("confidence", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_add_knowledge_with_confidence(
        self, empty_memory: CharacterMemory, confidence: float
    ):
        """Knowledge confidence levels are stored correctly."""
        empty_memory.add_knowledge(
            fact="Something uncertain",
            confidence=confidence,
        )

        assert empty_memory.knowledge[0].confidence == confidence

    def test_add_multiple_knowledge_items(self, empty_memory: CharacterMemory):
        """Multiple knowledge items can be added."""
        empty_memory.add_knowledge(fact="Fact 1")
        empty_memory.add_knowledge(fact="Fact 2")
        empty_memory.add_knowledge(fact="Fact 3")

        assert len(empty_memory.knowledge) == 3


class TestCharacterMemoryUpdateRelationship:
    """Tests for CharacterMemory.update_relationship()."""

    def test_update_relationship_creates_new(self, empty_memory: CharacterMemory):
        """Creates a new relationship if it doesn't exist."""
        empty_memory.update_relationship("Alice")

        assert "Alice" in empty_memory.relationships
        assert empty_memory.relationships["Alice"].character_name == "Alice"
        assert empty_memory.relationships["Alice"].sentiment == "neutral"
        assert empty_memory.relationships["Alice"].trust_level == 0.5

    def test_update_relationship_changes_sentiment(self, empty_memory: CharacterMemory):
        """Can change the sentiment of a relationship."""
        empty_memory.update_relationship("Alice")
        empty_memory.update_relationship("Alice", sentiment="positive")

        assert empty_memory.relationships["Alice"].sentiment == "positive"

    def test_update_relationship_trust_increases(self, empty_memory: CharacterMemory):
        """Trust level increases with positive delta."""
        empty_memory.update_relationship("Alice")  # trust = 0.5
        empty_memory.update_relationship("Alice", trust_delta=0.2)

        assert empty_memory.relationships["Alice"].trust_level == pytest.approx(0.7)

    def test_update_relationship_trust_decreases(self, empty_memory: CharacterMemory):
        """Trust level decreases with negative delta."""
        empty_memory.update_relationship("Alice")  # trust = 0.5
        empty_memory.update_relationship("Alice", trust_delta=-0.2)

        assert empty_memory.relationships["Alice"].trust_level == pytest.approx(0.3)

    def test_update_relationship_trust_clamped_at_zero(
        self, empty_memory: CharacterMemory
    ):
        """Trust level cannot go below 0.0."""
        empty_memory.update_relationship("Alice")  # trust = 0.5
        empty_memory.update_relationship("Alice", trust_delta=-1.0)

        assert empty_memory.relationships["Alice"].trust_level == 0.0

    def test_update_relationship_trust_clamped_at_one(
        self, empty_memory: CharacterMemory
    ):
        """Trust level cannot go above 1.0."""
        empty_memory.update_relationship("Alice")  # trust = 0.5
        empty_memory.update_relationship("Alice", trust_delta=1.0)

        assert empty_memory.relationships["Alice"].trust_level == 1.0

    @pytest.mark.parametrize(
        "initial_trust_delta,delta,expected",
        [
            (0.0, 0.0, 0.5),  # No change
            (0.0, 0.3, 0.8),  # Increase
            (0.0, -0.3, 0.2),  # Decrease
            (-0.2, -0.5, 0.0),  # Clamped at 0 (0.3 - 0.5 = 0)
            (0.3, 0.5, 1.0),  # Clamped at 1 (0.8 + 0.5 = 1)
        ],
    )
    def test_update_relationship_trust_bounds_parametrized(
        self,
        empty_memory: CharacterMemory,
        initial_trust_delta: float,
        delta: float,
        expected: float,
    ):
        """Trust level is clamped between 0.0 and 1.0."""
        empty_memory.update_relationship("Alice", trust_delta=initial_trust_delta)
        empty_memory.update_relationship("Alice", trust_delta=delta)

        assert empty_memory.relationships["Alice"].trust_level == pytest.approx(
            expected
        )

    def test_update_relationship_adds_note(self, empty_memory: CharacterMemory):
        """Notes are appended to the relationship."""
        empty_memory.update_relationship("Alice")
        empty_memory.update_relationship("Alice", note="First meeting")
        empty_memory.update_relationship("Alice", note="Had coffee together")

        assert empty_memory.relationships["Alice"].notes == [
            "First meeting",
            "Had coffee together",
        ]

    def test_update_relationship_none_note_not_added(
        self, empty_memory: CharacterMemory
    ):
        """None note is not added to notes list."""
        empty_memory.update_relationship("Alice", note=None)

        assert empty_memory.relationships["Alice"].notes == []


class TestCharacterMemoryGetSummary:
    """Tests for CharacterMemory.get_summary()."""

    def test_get_summary_empty_memory(self, empty_memory: CharacterMemory):
        """Empty memory returns minimal summary with emotional state."""
        summary = empty_memory.get_summary()

        assert "Current emotional state: neutral" in summary
        assert "Recent events:" not in summary

    def test_get_summary_with_events(self, empty_memory: CharacterMemory):
        """Summary includes recent events."""
        empty_memory.add_interaction(event_type="spoke", content="Hello there!")
        summary = empty_memory.get_summary()

        assert "Recent events:" in summary
        assert "[spoke]" in summary
        assert "Hello there!" in summary

    def test_get_summary_short_content_includes_ellipsis(
        self, empty_memory: CharacterMemory
    ):
        """Even short content still includes ellipsis in summary formatting."""
        empty_memory.add_interaction(event_type="spoke", content="Hi")
        summary = empty_memory.get_summary()

        assert "Hi" in summary
        assert "Hi..." in summary

    def test_get_summary_max_events_parameter(self, empty_memory: CharacterMemory):
        """Summary respects max_events parameter."""
        for i in range(10):
            empty_memory.add_interaction(event_type="spoke", content=f"Event {i}")

        summary = empty_memory.get_summary(max_events=3)

        # Should only show last 3 events (7, 8, 9)
        assert "Event 7" in summary
        assert "Event 8" in summary
        assert "Event 9" in summary
        assert "Event 0" not in summary

    def test_get_summary_truncates_content_at_80_chars(
        self, empty_memory: CharacterMemory
    ):
        """Event content in summary is truncated to 80 chars."""
        long_content = "x" * 100
        empty_memory.add_interaction(event_type="spoke", content=long_content)
        summary = empty_memory.get_summary()

        # Content should be truncated with "..."
        assert "x" * 80 in summary
        assert "x" * 81 not in summary

    def test_get_summary_shows_knowledge_count(self, empty_memory: CharacterMemory):
        """Summary shows count of knowledge items."""
        empty_memory.add_knowledge(fact="Fact 1")
        empty_memory.add_knowledge(fact="Fact 2")
        empty_memory.add_knowledge(fact="Fact 3")

        summary = empty_memory.get_summary()

        assert "Known facts: 3 items" in summary

    def test_get_summary_shows_relationships(self, empty_memory: CharacterMemory):
        """Summary includes relationship info."""
        empty_memory.update_relationship("Alice", sentiment="positive")
        empty_memory.update_relationship("Bob", sentiment="negative")

        summary = empty_memory.get_summary()

        assert "Relationships:" in summary
        assert "Alice: positive" in summary
        assert "Bob: negative" in summary

    def test_get_summary_shows_current_emotional_state(
        self, empty_memory: CharacterMemory
    ):
        """Summary always includes current emotional state."""
        empty_memory.add_interaction(
            event_type="witnessed",
            content="Something amazing",
            emotional_state="joyful",
        )
        summary = empty_memory.get_summary()

        assert "Current emotional state: joyful" in summary


class TestCharacterMemoryGetEmotionalArc:
    """Tests for CharacterMemory.get_emotional_arc()."""

    def test_get_emotional_arc_empty(self, empty_memory: CharacterMemory):
        """Empty emotional arc returns stable message."""
        result = empty_memory.get_emotional_arc()

        assert result == "Emotional state has remained stable."

    def test_get_emotional_arc_single_state(self, empty_memory: CharacterMemory):
        """Single emotional state is shown."""
        empty_memory.add_interaction(
            event_type="witnessed",
            content="Something happened",
            emotional_state="happy",
        )
        result = empty_memory.get_emotional_arc()

        assert "Recent emotional states:" in result
        assert "happy" in result

    def test_get_emotional_arc_multiple_states(self, empty_memory: CharacterMemory):
        """Multiple emotional states are shown with arrows."""
        states = ["happy", "sad", "angry", "calm"]
        for state in states:
            empty_memory.add_interaction(
                event_type="felt",
                content=f"Feeling {state}",
                emotional_state=state,
            )
        result = empty_memory.get_emotional_arc()

        assert "happy -> sad -> angry -> calm" in result

    def test_get_emotional_arc_shows_last_5_only(self, empty_memory: CharacterMemory):
        """Only the last 5 emotional states are shown."""
        states = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]
        for state in states:
            empty_memory.add_interaction(
                event_type="felt",
                content=f"State {state}",
                emotional_state=state,
            )
        result = empty_memory.get_emotional_arc()

        # Should only have last 5: s3, s4, s5, s6, s7
        assert "s3 -> s4 -> s5 -> s6 -> s7" in result
        assert "s1" not in result
        assert "s2" not in result


class TestCharacterMemoryIsolation:
    """Tests for mutable default isolation."""

    def test_memory_instances_do_not_share_mutable_defaults(self):
        """Lists and dicts should not be shared across instances."""
        memory_a = CharacterMemory()
        memory_b = CharacterMemory()

        memory_a.add_interaction(event_type="spoke", content="Hello")
        memory_a.add_knowledge(fact="Fact")
        memory_a.update_relationship("Alice", sentiment="positive")

        assert len(memory_a.events) == 1
        assert len(memory_a.knowledge) == 1
        assert "Alice" in memory_a.relationships

        assert len(memory_b.events) == 0
        assert len(memory_b.knowledge) == 0
        assert memory_b.relationships == {}
