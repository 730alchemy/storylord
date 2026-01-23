"""LangGraph tool-calling loop utilities."""

from __future__ import annotations

import json
import operator
from typing import Annotated, Any

import structlog
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.channels import UntrackedValue
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from tools.context import ToolExecutionContext
from tools.registry import ToolRegistry

log = structlog.get_logger(__name__)


class ToolLoopState(TypedDict):
    """State for a tool-calling LLM loop."""

    messages: Annotated[list[BaseMessage], operator.add]
    tool_registry: Annotated[ToolRegistry | None, UntrackedValue]
    tool_context: Annotated[ToolExecutionContext | None, UntrackedValue]
    tool_call_log: Annotated[list[dict], operator.add]


def build_tool_loop(llm):
    """Build a LangGraph loop that executes tool calls from an LLM."""

    def llm_node(state: ToolLoopState) -> dict:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    def action_node(state: ToolLoopState) -> dict:
        tool_registry = state.get("tool_registry")
        tool_context = state.get("tool_context")
        messages = state.get("messages", [])
        if not messages:
            return {}

        last = messages[-1]
        tool_calls = getattr(last, "tool_calls", None) or []
        if not tool_calls:
            return {}

        if tool_registry and tool_context:
            tool_registry.configure(tool_context)

        tool_messages: list[ToolMessage] = []
        records: list[dict] = []

        for idx, call in enumerate(tool_calls):
            if isinstance(call, dict):
                name_value = call.get("name")
                args = call.get("args") or {}
                call_id = call.get("id") or f"{name_value}-{idx}"
            else:
                name_value = getattr(call, "name", None)
                args = getattr(call, "args", {}) or {}
                call_id = getattr(call, "id", None) or f"{name_value}-{idx}"

            try:
                if not tool_registry:
                    raise RuntimeError("Tool registry not available.")
                result = tool_registry.execute(name_value, **args)
                payload = _coerce_tool_payload(result)
                content = payload if isinstance(payload, str) else json.dumps(payload)
                tool_messages.append(ToolMessage(content=content, tool_call_id=call_id))
                records.append(
                    _build_record(
                        name_value,
                        args,
                        payload,
                        tool_context,
                        tool_call_id=call_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                error_payload = {"error": str(exc)}
                log.exception(
                    "tool_execution_failed",
                    tool=name_value,
                    tool_input=args,
                    run_id=tool_context.run_id if tool_context else None,
                    trace_id=tool_context.trace_id if tool_context else None,
                    beat_reference=tool_context.beat_reference
                    if tool_context
                    else None,
                )
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(error_payload),
                        tool_call_id=call_id,
                    )
                )
                records.append(
                    _build_record(
                        name_value,
                        args,
                        error_payload,
                        tool_context,
                        tool_call_id=call_id,
                    )
                )

        log.info(
            "tool_action_complete",
            tool_calls=len(tool_messages),
            run_id=tool_context.run_id if tool_context else None,
            trace_id=tool_context.trace_id if tool_context else None,
            beat_reference=tool_context.beat_reference if tool_context else None,
        )

        return {"messages": tool_messages, "tool_call_log": records}

    def should_continue(state: ToolLoopState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last = messages[-1]
        tool_calls = getattr(last, "tool_calls", None) or []
        return "action" if tool_calls else "end"

    builder = StateGraph(ToolLoopState)
    builder.add_node("llm", llm_node)
    builder.add_node("action", action_node)
    builder.add_edge(START, "llm")
    builder.add_conditional_edges(
        "llm",
        should_continue,
        {"action": "action", "end": END},
    )
    builder.add_edge("action", "llm")

    return builder.compile(checkpointer=False)


def _coerce_tool_payload(result: Any) -> dict | str:
    if isinstance(result, str):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return {"result": result}


def _build_record(
    tool_name: str | None,
    tool_input: dict,
    tool_output: dict | str,
    context: ToolExecutionContext | None,
    tool_call_id: str | None = None,
) -> dict:
    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "tool_call_id": tool_call_id,
        "run_id": context.run_id if context else None,
        "trace_id": context.trace_id if context else None,
        "beat_reference": context.beat_reference if context else None,
    }
