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
