from __future__ import annotations

from typing import Any

from tools.context import ToolExecutionContext
from tools.registry import ToolRegistry


class DummyTool:
    name = "dummy"
    description = "A dummy tool"

    def __init__(self) -> None:
        self.configured = False
        self.context = None

    def get_schema(self) -> dict:
        return {"type": "object", "properties": {"x": {"type": "integer"}}}

    def configure(self, context: ToolExecutionContext) -> None:
        self.configured = True
        self.context = context

    def execute(self, **params: Any) -> Any:
        return {"ok": params}


class OtherTool(DummyTool):
    name = "other"


def test_registry_skips_unknown_tools(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.registry.discover_tools",
        lambda: {"dummy": DummyTool, "other": OtherTool},
    )

    registry = ToolRegistry(["dummy", "missing"])

    assert len(registry) == 1
    assert "dummy" in registry
    assert "missing" not in registry


def test_registry_configure_calls_tools(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.registry.discover_tools",
        lambda: {"dummy": DummyTool},
    )

    registry = ToolRegistry(["dummy"])
    context = ToolExecutionContext(run_id="run")
    registry.configure(context)

    tool = registry.get("dummy")
    assert tool.configured is True
    assert tool.context == context


def test_registry_list_tools(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.registry.discover_tools",
        lambda: {"dummy": DummyTool},
    )

    registry = ToolRegistry(["dummy"])
    schemas = registry.list_tools()

    assert schemas == [
        {
            "name": "dummy",
            "description": "A dummy tool",
            "parameters": {"type": "object", "properties": {"x": {"type": "integer"}}},
        }
    ]


def test_registry_execute(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.registry.discover_tools",
        lambda: {"dummy": DummyTool},
    )

    registry = ToolRegistry(["dummy"])
    result = registry.execute("dummy", x=1)

    assert result == {"ok": {"x": 1}}
