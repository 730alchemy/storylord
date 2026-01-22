# ADR: Narrator–Character Dialogue Orchestration (Design 3)

## Objective
Ensure the narrator agent uses character agents to generate dialogue for speaking characters while maximizing story quality (entertainment value, fidelity to character voice/values, flexible and imaginative narration, reader captivation).

## Constraints
- Designs 1 and 4 are explicitly rejected.
- Start with Design 3 to explore tool-driven creativity and observe emergent narrative behavior.
- Detailed auditing is required (prompts used, tools called, context info).
- Code-side enforcement is deferred for now; prioritize creativity and monitor outcomes.
- Designs 5 and 6 are future options for users.
- Risk: narrator guidance can conflict with character values/goals/traits.
- Risk: post-processing to smooth narration/dialogue can introduce complexity and new inconsistencies.

## Options

### Design 1 — Narrator inserts dialogue directly (no character-agent calls)
**Summary from conversation**
The narrator decides when a character should speak and writes the dialogue itself, then continues the narrative.

**Pros**
- Simple flow; fewer calls and less orchestration overhead.

**Cons**
- Rejected for quality and creativity goals; does not ensure character agents control dialogue.
- Provides no opportunity to explore tool-based creativity.

### Design 2 — Narrator gives guidance; character agent writes dialogue; code reconciles and smooths
**Summary from conversation**
Narrator provides motivations/guidance; character agent outputs dialogue; a separate pass reconciles narration and dialogue to smooth inconsistencies.

**Pros**
- Attempts tighter alignment between narration and dialogue.

**Cons**
- Too complex; reconciliation loops can create more disconnects and rough patches.
- Higher risk of wasted calls if smoothing reveals earlier dialogue changes.
- Narrator guidance may conflict with character values/personality, creating mismatch.

### Design 3 — Narrator uses tools to call character agents during generation
**Summary from conversation**
The narrator LLM decides when to invoke a character dialogue tool for characters that have agents; the narrator adapts the narrative based on returned dialogue.

**Pros**
- Strong creativity potential; narrator can adapt to actual character responses.
- Highest alignment with story-quality priority (entertainment, fidelity, captivation).

**Cons**
- Less controllable; tool usage can be unpredictable.
- Harder to guarantee correct tool use without code-side enforcement.
- Requires robust auditing to diagnose outcomes.

### Design 4 — External orchestration decides dialogue slots; narrator fills around them
**Summary from conversation**
An external system preplans dialogue slots and the narrator fills in around them.

**Pros**
- More structural control.

**Cons**
- Rejected as too rigid and restrictive for creative goals.

### Design 5 — Multi-pass or collaborative drafting variants
**Summary from conversation**
Alternative orchestration modes that may introduce additional creative or collaborative passes.

**Pros**
- Potential for high creativity and exploration.

**Cons**
- More complex; unclear control guarantees.

### Design 6 — Alternative creative mixing (branching/ensemble/adaptive agent modes)
**Summary from conversation**
Additional creative modes that blend agents or branching narrative strategies.

**Pros**
- Strong creative potential and user-facing variety.

**Cons**
- Added complexity; control risks similar to Design 5.

## Decision
Adopt **Design 3** as the initial implementation. Prioritize creativity and allow the narrator to call character-agent tools during generation. Monitor quality and outcomes via detailed auditing (prompts, tool calls, context info). Defer code-side enforcement unless outcomes warrant it.

## Consequences
- Increased reliance on tool-call behavior and model compliance.
- Requires auditing infrastructure from the start.
- Potential for emergent narrative improvements, but with less deterministic control.

## Future Considerations
- Offer Designs 5 and 6 as user-selectable modes.
- Add enforcement or stricter constraints if tool usage becomes unreliable.
- Develop evaluation criteria for character fidelity and narrative cohesion.

## Open Questions
- What is the minimal auditing schema needed for reliable diagnosis?
- How should tool-call misuse or missing calls be detected?
- What metrics best capture “story quality” in this system?
