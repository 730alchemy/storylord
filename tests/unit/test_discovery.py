from __future__ import annotations

import pytest

import agents.discovery as agent_discovery
import tools.discovery as tool_discovery


class DummyTool:
    def __init__(self) -> None:
        self.created = True


class DummyArchitect:
    pass


class DummyNarrator:
    pass


class DummyEditor:
    pass


class DummyCharacterAgentType:
    def __init__(self) -> None:
        self.name = "dummy"


class DummyEP:
    def __init__(self, name: str, obj):
        self.name = name
        self._obj = obj

    def load(self):
        return self._obj


def test_tool_discovery_and_get(monkeypatch):
    def fake_entry_points(group=None):
        if group == "storylord.tools":
            return [DummyEP("alpha", DummyTool), DummyEP("beta", DummyTool)]
        return []

    monkeypatch.setattr(tool_discovery, "entry_points", fake_entry_points)

    tools = tool_discovery.discover_tools()
    assert set(tools.keys()) == {"alpha", "beta"}

    assert tool_discovery.list_tools() == ["alpha", "beta"]
    assert isinstance(tool_discovery.get_tool("alpha"), DummyTool)

    with pytest.raises(ValueError, match="Unknown tool"):
        tool_discovery.get_tool("missing")


def test_agent_discovery_and_get(monkeypatch):
    def fake_entry_points(group=None):
        if group == "storylord.architects":
            return [DummyEP("arch", DummyArchitect)]
        if group == "storylord.narrators":
            return [DummyEP("nar", DummyNarrator)]
        if group == "storylord.editors":
            return [DummyEP("ed", DummyEditor)]
        if group == "storylord.character_agents":
            return [DummyEP("char", DummyCharacterAgentType)]
        return []

    monkeypatch.setattr(agent_discovery, "entry_points", fake_entry_points)

    assert list(agent_discovery.discover_architects().keys()) == ["arch"]
    assert list(agent_discovery.discover_narrators().keys()) == ["nar"]
    assert list(agent_discovery.discover_editors().keys()) == ["ed"]
    assert list(agent_discovery.discover_character_agent_types().keys()) == ["char"]

    assert isinstance(agent_discovery.get_architect("arch"), DummyArchitect)
    assert isinstance(agent_discovery.get_narrator("nar"), DummyNarrator)
    assert isinstance(agent_discovery.get_editor("ed"), DummyEditor)
    assert isinstance(
        agent_discovery.get_character_agent_type("char"), DummyCharacterAgentType
    )

    assert agent_discovery.list_architects() == ["arch"]
    assert agent_discovery.list_narrators() == ["nar"]
    assert agent_discovery.list_editors() == ["ed"]
    assert agent_discovery.list_character_agent_types() == ["char"]

    with pytest.raises(ValueError, match="Unknown architect"):
        agent_discovery.get_architect("missing")

    with pytest.raises(ValueError, match="Unknown narrator"):
        agent_discovery.get_narrator("missing")

    with pytest.raises(ValueError, match="Unknown editor"):
        agent_discovery.get_editor("missing")

    with pytest.raises(ValueError, match="Unknown character agent type"):
        agent_discovery.get_character_agent_type("missing")
