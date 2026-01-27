from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from graph.tool_loop import _build_record, _coerce_tool_payload, build_tool_loop
from tools.context import ToolExecutionContext


class DummyModel:
    def model_dump(self) -> dict:
        return {"value": 42}


def test_coerce_tool_payload_variants():
    assert _coerce_tool_payload("text") == "text"
    assert _coerce_tool_payload({"a": 1}) == {"a": 1}
    assert _coerce_tool_payload(DummyModel()) == {"value": 42}
    assert _coerce_tool_payload(7) == {"result": 7}


def test_build_record_includes_context_fields():
    context = ToolExecutionContext(
        character_registry=None,
        run_id="run",
        trace_id="trace",
        beat_reference="beat",
    )
    record = _build_record(
        tool_name="tool",
        tool_input={"x": 1},
        tool_output={"y": 2},
        context=context,
        tool_call_id="call-1",
    )

    assert record["tool_name"] == "tool"
    assert record["tool_input"] == {"x": 1}
    assert record["tool_output"] == {"y": 2}
    assert record["tool_call_id"] == "call-1"
    assert record["run_id"] == "run"
    assert record["trace_id"] == "trace"
    assert record["beat_reference"] == "beat"


@dataclass
class DummyRegistry:
    context: ToolExecutionContext | None = None

    def configure(self, context: ToolExecutionContext) -> None:
        self.context = context

    def execute(self, name: str, **params: Any) -> Any:
        if name == "fail":
            raise RuntimeError("boom")
        return {"ok": params}


class DummyLLM:
    def __init__(self, tool_name: str = "echo") -> None:
        self.tool_name = tool_name
        self.calls = 0

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="tool call",
                tool_calls=[
                    {"name": self.tool_name, "args": {"text": "hi"}, "id": "1"}
                ],
            )
        return AIMessage(content="done")


def test_tool_loop_success_path():
    registry = DummyRegistry()
    tool_context = ToolExecutionContext(run_id="run", trace_id="trace")
    graph = build_tool_loop(DummyLLM())

    result = graph.invoke(
        {
            "messages": [HumanMessage(content="start")],
            "tool_registry": registry,
            "tool_context": tool_context,
            "tool_call_log": [],
        }
    )

    assert registry.context == tool_context
    assert len(result["tool_call_log"]) == 1

    record = result["tool_call_log"][0]
    assert record["tool_name"] == "echo"
    assert record["tool_input"] == {"text": "hi"}
    assert record["tool_output"] == {"ok": {"text": "hi"}}

    assert any(isinstance(message, ToolMessage) for message in result["messages"])


def test_tool_loop_error_path():
    registry = DummyRegistry()
    tool_context = ToolExecutionContext(run_id="run", trace_id="trace")
    graph = build_tool_loop(DummyLLM(tool_name="fail"))

    result = graph.invoke(
        {
            "messages": [HumanMessage(content="start")],
            "tool_registry": registry,
            "tool_context": tool_context,
            "tool_call_log": [],
        }
    )

    record = result["tool_call_log"][0]
    assert record["tool_name"] == "fail"
    assert record["tool_output"] == {"error": "boom"}

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert tool_messages
    payload = json.loads(tool_messages[-1].content)
    assert "error" in payload
