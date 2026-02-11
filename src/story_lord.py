import argparse
import uuid

import structlog
import yaml

from bootstrap import bootstrap
from graph import build_story_generation_graph
from models import StoryInput

log = structlog.get_logger(__name__)


def run_story_generation(
    input_file: str, thread_id: str | None = None, checkpointer=None
) -> dict:
    """Generate a story from the given input file.

    Args:
        input_file: Path to YAML file with story parameters.
        thread_id: Optional thread ID for checkpointing. Defaults to random UUID.
        checkpointer: Optional checkpointer for persistence.

    Returns:
        Final state values from the graph.
    """
    # Load input
    with open(input_file) as f:
        story_input = StoryInput.model_validate(yaml.safe_load(f))

    graph = build_story_generation_graph(checkpointer)
    thread_id = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "story_input": story_input,
        "run_id": "",
        "tool_registry": None,
        "character_registry": None,
        "architecture": None,
        "narrated_story": None,
        "edited_narrations": [],
        "edit_history": [],
        "current_narration_index": 0,
        "output_dir": "output",
        "architecture_saved": False,
        "narrative_saved": False,
    }

    try:
        for event in graph.stream(initial_state, config=config):
            log.info("node_completed", node=list(event.keys())[0])
    except Exception:  # noqa: BLE001
        log.exception("story_generation_failed")
        raise

    return graph.get_state(config).values


def run_tui() -> None:
    """Launch the TUI application."""
    from tui import StoryLordApp

    app = StoryLordApp()
    app.run()


def main():
    bootstrap()
    parser = argparse.ArgumentParser(description="AI-powered story generation")
    parser.add_argument("-f", "--file", help="YAML file with story parameters")
    args = parser.parse_args()

    if args.file:
        run_story_generation(args.file)
    else:
        run_tui()


if __name__ == "__main__":
    main()
