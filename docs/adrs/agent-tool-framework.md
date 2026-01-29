# ADR: Storylord Tool Framework that Accommodates Tools that Call Agents

## Objective
Define a tool framework for the entire Storylord application that meets these requirements:

- enable tools to call other agents
- preserve and isolate tool-embedded agent memory during a run
- align with LangChain and LangGraph
- support clear, easy auditing and tracing

## Constraints
- Must continue using LangChain and LangGraph.
- Tools must be able to invoke other agents (agent-to-agent calls).
- Agents must retain memory across a run of Storylord.
- Auditing and tracing must be first-class and easy to follow.
- Favor creative flexibility now; stricter enforcement can come later if needed.

## Options

### Incrementally improve the existing Tool Registry
**Summary from conversation**
Keep the current Tool Registry and entry-point discovery, while adding context injection and custom orchestration to enable agent-calling tools and auditing.

**Pros**
- Minimal migration; preserves entry-point discovery and existing logging patterns.
- Straightforward to add runtime context injection for agent access and memory.

**Cons**
- Requires custom orchestration/tool-calling loop and audit conventions.

### Use native LangChain tools only (AgentExecutor loop)
**Summary from conversation**
Rely entirely on LangChain tool binding and AgentExecutor-driven loops, minimizing custom tooling.

**Pros**
- First-class LangChain integration with a “single-call” feel.
- Simple tool binding in the LLM stack.

**Cons**
- Harder to inject shared Storylord runtime context and live agent registries.
- Auditing depends on LangChain callback plumbing.
- Likely requires per-run tool construction or global state.

### LangGraph Action/Tool node pattern
**Summary from conversation**
Adopt the LangGraph agent loop pattern where the narrator (and other agents) emit tool calls, a tool/action node executes them, and results are fed back into the LLM.

**Pros**
- Explicit control over orchestration with clean tracing.
- Natural place to resolve tool → agent calls.
- Good fit for memory-aware workflows and per-run state.

**Cons**
- More refactor; explicit tool-calling loop.
- Some agents may need to shift from structured outputs to message-based tool calls.

### Deepagents (LangChain)
**Summary from conversation**
Use LangChain deepagents for built-in subagent delegation with LangGraph under the hood.

**Pros**
- Built-in subagents/delegation for agent-to-agent calls.
- Compatible with LangGraph and supports context isolation.

**Cons**
- Extra harness; default prompts/tooling not narrative-optimized.
- Potential overhead for non-narrator tooling.

## Decision
Adopt the **LangGraph Action/Tool node pattern** as the foundation for Storylord’s tool framework. Tools will be able to call other agents while retaining memory during a run, and the action node will provide clear auditing and tracing of tool calls and results.

## Consequences
- Storylord gains explicit, traceable tool orchestration aligned with LangGraph.
- Some agent flows may require refactoring to support tool-calling messages.
- Tool execution becomes a central integration point for agent-to-agent calls.

## Future Considerations
- Standardize audit logging schema and trace IDs for tool calls.
- Decide memory scoping rules (thread vs story run) and persistence strategy.
- Add enforcement or guardrails if tool usage becomes unreliable.

## Open Questions
- How should runtime context be injected into tool execution?
- What state shape best supports the tool/action loop across agents?
- What minimal audit events are required for reliable traceability?
