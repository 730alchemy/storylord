from __future__ import annotations

import importlib
from pathlib import Path

import yaml


def _write_story_input(path: Path) -> None:
    payload = {
        "story_idea": "Idea",
        "characters": [
            {
                "name": "Test",
                "description": "Desc",
                "role": "protagonist",
                "motivations": "Motivation",
                "relationships": "None",
                "backstory": "Backstory",
            }
        ],
        "num_plot_events": 1,
        "beats_per_event": [1, 1],
        "tone": "tone",
        "output_file": "output",
    }
    path.write_text(yaml.safe_dump(payload))


class DummyGraph:
    def __init__(self) -> None:
        self.initial_state = None
        self.config = None

    def stream(self, initial_state, config=None):
        self.initial_state = initial_state
        self.config = config
        yield {"load_input": None}

    def get_state(self, config=None):
        class DummyState:
            def __init__(self, values):
                self.values = values

        return DummyState(
            {"final": "ok", "thread_id": config["configurable"]["thread_id"]}
        )


def test_run_story_generation_uses_thread_id(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    import story_lord

    importlib.reload(story_lord)

    dummy_graph = DummyGraph()
    monkeypatch.setattr(
        story_lord,
        "build_story_generation_graph",
        lambda _checkpointer=None: dummy_graph,
    )

    input_path = tmp_path / "input.yaml"
    _write_story_input(input_path)

    result = story_lord.run_story_generation(str(input_path), thread_id="thread-123")

    assert result == {"final": "ok", "thread_id": "thread-123"}
    assert dummy_graph.config["configurable"]["thread_id"] == "thread-123"
    assert dummy_graph.initial_state["output_dir"] == "output"
    assert dummy_graph.initial_state["edited_narrations"] == []
    assert dummy_graph.initial_state["edit_history"] == []
