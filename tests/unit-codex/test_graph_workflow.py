"""Tests for graph/workflow.py."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from graph.workflow import build_story_generation_graph


class TestBuildStoryGenerationGraph:
    """Tests for graph construction."""

    def test_graph_compiles_with_default_checkpointer(self):
        """Graph should compile successfully with default MemorySaver."""
        graph = build_story_generation_graph()
        assert graph is not None

    def test_graph_compiles_with_custom_checkpointer(self):
        """Graph should compile with a custom checkpointer."""
        custom_checkpointer = MemorySaver()
        graph = build_story_generation_graph(checkpointer=custom_checkpointer)
        assert graph is not None

    def test_graph_compiles_with_none_checkpointer(self):
        """Graph should use default when None is passed."""
        graph = build_story_generation_graph(checkpointer=None)
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        """Graph should have all expected nodes."""
        graph = build_story_generation_graph()

        # Get the node names from the graph
        # LangGraph's get_graph() returns a DrawableGraph with nodes as a dict
        graph_repr = graph.get_graph()

        # nodes is a dict-like structure, get keys
        if hasattr(graph_repr.nodes, "keys"):
            node_names = set(graph_repr.nodes.keys())
        else:
            # Fallback: nodes might be iterable of strings directly
            node_names = set(graph_repr.nodes)

        expected_nodes = {
            "__start__",
            "__end__",
            "load_input",
            "architect",
            "save_architecture",
            "narrator",
            "editor",
            "save_narrative",
        }

        assert expected_nodes.issubset(node_names), (
            f"Missing nodes: {expected_nodes - node_names}"
        )

    def test_graph_has_expected_edges(self):
        """Graph should have correct edge connections."""
        graph = build_story_generation_graph()
        graph_repr = graph.get_graph()

        # Build edge set from graph representation
        # edges can be tuples or objects with source/target
        edges = set()
        for edge in graph_repr.edges:
            if hasattr(edge, "source") and hasattr(edge, "target"):
                edges.add((edge.source, edge.target))
            elif isinstance(edge, tuple) and len(edge) >= 2:
                edges.add((edge[0], edge[1]))

        # Check critical edges exist
        assert ("__start__", "load_input") in edges
        assert ("load_input", "architect") in edges
        assert ("architect", "save_architecture") in edges
        assert ("save_architecture", "narrator") in edges
        assert ("narrator", "editor") in edges
        assert ("save_narrative", "__end__") in edges

    def test_graph_has_conditional_edge_from_editor(self):
        """Editor node should have conditional edges."""
        graph = build_story_generation_graph()
        graph_repr = graph.get_graph()

        # Find edges from editor
        editor_targets = set()
        for edge in graph_repr.edges:
            source = edge.source if hasattr(edge, "source") else edge[0]
            target = edge.target if hasattr(edge, "target") else edge[1]
            if source == "editor":
                editor_targets.add(target)

        # Editor should be able to go to either itself or save_narrative
        assert "editor" in editor_targets or "save_narrative" in editor_targets
