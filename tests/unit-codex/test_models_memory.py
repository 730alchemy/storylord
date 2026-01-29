from models import CharacterMemory


def test_add_interaction_records_event_and_emotion():
    memory = CharacterMemory()
    long_text = "A" * 150

    memory.add_interaction(
        event_type="spoke",
        content=long_text,
        scene_reference="scene-1",
        other_characters=None,
        emotional_state="excited",
    )

    assert len(memory.events) == 1
    event = memory.events[0]
    assert event.event_type == "spoke"
    assert event.content == long_text
    assert event.scene_reference == "scene-1"
    assert event.other_characters == []

    assert memory.current_emotional_state == "excited"
    assert len(memory.emotional_arc) == 1
    snapshot = memory.emotional_arc[0]
    assert snapshot.state == "excited"
    assert snapshot.trigger == long_text[:100]


def test_add_interaction_without_emotion_does_not_update_arc():
    memory = CharacterMemory()
    memory.add_interaction(event_type="thought", content="testing")

    assert len(memory.events) == 1
    assert memory.current_emotional_state == "neutral"
    assert memory.emotional_arc == []


def test_update_relationship_creates_and_clamps_values():
    memory = CharacterMemory()

    memory.update_relationship(
        "Jasper",
        sentiment="positive",
        trust_delta=0.7,
        note="Helped in a crisis",
    )

    rel = memory.relationships["Jasper"]
    assert rel.sentiment == "positive"
    assert rel.trust_level == 1.0
    assert rel.notes == ["Helped in a crisis"]

    memory.update_relationship("Jasper", trust_delta=-2.0)
    assert memory.relationships["Jasper"].trust_level == 0.0


def test_get_summary_includes_recent_events_and_metadata():
    memory = CharacterMemory()
    memory.add_interaction(event_type="spoke", content="Hello" * 20)
    memory.add_interaction(event_type="thought", content="Something else" * 10)
    memory.add_knowledge("Secret passage")
    memory.update_relationship("Riley", sentiment="conflicted")

    summary = memory.get_summary(max_events=1)

    assert "Recent events:" in summary
    assert "[thought]" in summary
    assert "Known facts: 1 items" in summary
    assert "Relationships: Riley: conflicted" in summary
    assert "Current emotional state" in summary


def test_get_emotional_arc_variants():
    memory = CharacterMemory()

    assert memory.get_emotional_arc() == "Emotional state has remained stable."

    memory.add_interaction(event_type="spoke", content="first", emotional_state="happy")
    memory.add_interaction(event_type="spoke", content="second", emotional_state="sad")

    arc = memory.get_emotional_arc()
    assert "happy" in arc
    assert "sad" in arc
    assert "->" in arc


def test_get_summary_empty_memory():
    """Empty memory should return a sensible default."""
    memory = CharacterMemory()
    summary = memory.get_summary()

    # Should still have emotional state even if empty
    assert "neutral" in summary.lower() or "no significant" in summary.lower()


def test_add_knowledge_with_all_parameters():
    """add_knowledge should accept source and confidence."""
    memory = CharacterMemory()

    memory.add_knowledge(
        fact="The treasure is hidden in the cave",
        source="overheard conversation",
        confidence=0.7,
    )

    assert len(memory.knowledge) == 1
    item = memory.knowledge[0]
    assert item.fact == "The treasure is hidden in the cave"
    assert item.source == "overheard conversation"
    assert item.confidence == 0.7


def test_add_knowledge_defaults():
    """add_knowledge should have sensible defaults."""
    memory = CharacterMemory()
    memory.add_knowledge("Simple fact")

    item = memory.knowledge[0]
    assert item.fact == "Simple fact"
    assert item.source == ""
    assert item.confidence == 1.0


def test_add_interaction_with_other_characters():
    """add_interaction should record other characters involved."""
    memory = CharacterMemory()

    memory.add_interaction(
        event_type="witnessed",
        content="Alice argued with Bob",
        other_characters=["Alice", "Bob"],
    )

    event = memory.events[0]
    assert event.other_characters == ["Alice", "Bob"]


def test_update_relationship_only_sentiment():
    """update_relationship with only sentiment should preserve trust."""
    memory = CharacterMemory()

    # First create relationship
    memory.update_relationship("Charlie", sentiment="neutral", trust_delta=0.0)
    assert memory.relationships["Charlie"].trust_level == 0.5  # default

    # Update only sentiment
    memory.update_relationship("Charlie", sentiment="positive")
    assert memory.relationships["Charlie"].sentiment == "positive"
    assert memory.relationships["Charlie"].trust_level == 0.5  # unchanged


def test_update_relationship_multiple_notes():
    """update_relationship should accumulate notes."""
    memory = CharacterMemory()

    memory.update_relationship("Diana", note="First meeting")
    memory.update_relationship("Diana", note="Had lunch together")
    memory.update_relationship("Diana", note="Helped with project")

    assert memory.relationships["Diana"].notes == [
        "First meeting",
        "Had lunch together",
        "Helped with project",
    ]


def test_get_summary_multiple_relationships():
    """get_summary should list all relationships."""
    memory = CharacterMemory()
    memory.update_relationship("Alice", sentiment="positive")
    memory.update_relationship("Bob", sentiment="negative")

    summary = memory.get_summary()
    assert "Alice" in summary
    assert "Bob" in summary
