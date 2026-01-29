# Unit Test Analysis: `tests/unit-codex/`

## 1. FRAGILITY

### String Literal Coupling (High Risk)
- `test_character_agents.py:49-54` - Tests are tightly coupled to exact trait description strings like `"passive, deferential, avoids confrontation"`. Any copywriting change breaks tests.
- `test_character_agents.py:80-103` - Same issue with MBTI dimension descriptions (e.g., `"Strongly introverted"`).
- `test_models_memory.py:67-71` - Asserts on exact strings like `"Recent events:"` and `"Known facts: 1 items"`.

### Module Reimport Pattern (Medium Risk)
- `test_config.py:14-15` and `test_story_lord.py:53-55` - Use `importlib.reload()` to force re-initialization. This is fragile because:
  - Module state leaks between tests if not properly isolated
  - Import order matters; other tests importing these modules first can cause failures
  - Parallel test execution becomes problematic

### Hardcoded Internal Implementation Details (Medium Risk)
- `test_graph_nodes.py:103` - Asserts `"character_speak" in result["tool_registry"].tool_names` - relies on internal field name
- `test_graph_nodes.py:162` - Filename pattern assertion `files[0].name.startswith("output_architecture_20240102_030405")` couples to exact timestamp format

---

## 2. DUPLICATION

### Repeated Fixture Patterns
- `DummyLLM` class is defined in both `test_character_agents.py:23-31` and `test_graph_tool_loop.py:62-76` with different signatures
- `DummyRegistry` class appears in `test_tools_character_speak.py:16-24` and `test_graph_tool_loop.py:49-59` with overlapping but inconsistent interfaces
- `DummyCharacter` class is defined in both `test_graph_nodes.py:39-42` and `test_tools_character_speak.py:10-13`

### Repeated `CharacterProfile` Construction
- `test_character_agents.py:35-43` - fixture `character_profile()`
- `test_graph_nodes.py:72-89` - `_make_story_input()` creates a similar profile inline
- Both construct nearly identical test data

### Monkeypatch Boilerplate
- The pattern `monkeypatch.setattr("graph.nodes.ToolRegistry", DummyToolRegistry)` and similar appear repeatedly without abstraction

---

## 3. GAPS IN COVERAGE

### Completely Untested Modules

| Module | Description |
|--------|-------------|
| `agents/character/registry.py` | CharacterRegistry class - creation, lookup, memory persistence, error cases |
| `agents/architect/architect_default.py` | Default architect agent |
| `agents/editor/editor_default.py` | Default editor |
| `agents/editor/editor_simile_smasher.py` | Simile-smasher editor |
| `agents/narrative/narrator_default.py` | Default narrator |
| `agents/character/protocols.py` | Protocol definitions |
| `agents/protocols.py` | Agent protocols |
| `graph/workflow.py` | Graph construction logic |
| `graph/state.py` | State type definitions |
| `tools/context.py` | ToolExecutionContext |

### Partially Tested - Missing Cases

**test_graph_nodes.py:**
- `architect_node()` - no test
- `narrator_node()` - no test
- `load_input_node()` with no character configs - no test
- Error paths when architect/narrator fail - no test

**test_tools_registry.py:**
- No test for `execute()` with unknown tool name
- No test for double-configure

**test_character_agents.py:**
- `BaseCharacterAgent.think()`, `choose()`, `answer()` methods - no tests
- Agent with initial_memory - no test

**test_models_memory.py:**
- `add_knowledge()` with source and confidence parameters - only tested once without parameters
- Memory events with `other_characters` populated - not tested
- `get_summary()` with empty memory - not tested

**test_discovery.py:**
- Entry point load failures - not tested
- Duplicate entry point names - not tested

### Edge Cases Not Covered
- Empty story input (no characters)
- Unicode/special characters in content
- Very long strings (truncation behavior)
- Concurrent access patterns
- Tool execution timeout/errors beyond basic "boom"

---

## 4. CORRECTNESS ISSUES

### Incomplete Assertions

`test_graph_tool_loop.py:79-101`:
```python
def test_tool_loop_success_path():
    # ...
    assert any(isinstance(message, ToolMessage) for message in result["messages"])
```
This only checks that *some* ToolMessage exists, not that it has the correct content or tool_call_id.

### Test Doesn't Match Production Behavior

`test_graph_nodes.py:109-128` - `test_editor_node_increments_and_records`:
```python
monkeypatch.setattr("graph.nodes.get_editor", lambda _name: DummyEditor("Edited"))
```
Production code at `nodes.py:149` hardcodes `get_editor("simile-smasher")`, but the test passes *any* editor name through. The test doesn't verify the correct editor is requested.

### State Mutation Not Verified

`test_story_lord.py:50-73` - The test verifies `dummy_graph.initial_state` but doesn't verify that the returned state from `get_state()` is actually used/returned correctly. The mock's `get_state` always returns what was configured, not what was actually processed.

### Missing Negative Assertions

`test_discovery.py:40-55` - Tests that `get_tool("missing")` raises, but doesn't verify the error message content or type specificity.

---

## SUGGESTIONS

1. **Extract Shared Fixtures** - Create a `tests/unit-codex/conftest.py` with shared dummy classes (`DummyLLM`, `DummyRegistry`, `DummyCharacter`) and common fixtures (`character_profile`, `story_input`).

2. **Reduce String Coupling** - For description/string tests, either:
   - Test that the function returns *something* non-empty
   - Use `assertIn` for key phrases rather than exact matches
   - Extract strings to constants shared between source and tests

3. **Add CharacterRegistry Tests** - This is a critical gap. The registry manages character lifecycle and memory persistence but has zero direct tests.

4. **Test the Graph Workflow** - `graph/workflow.py` builds the entire execution graph but has no tests. At minimum, test that the graph compiles and has expected nodes/edges.

5. **Replace Module Reload Pattern** - Instead of `importlib.reload()`, use dependency injection or module-level functions that accept configuration as parameters.

6. **Add Integration-Style Unit Tests** - Tests that exercise `load_input_node` -> `architect_node` -> `narrator_node` with minimal mocking would catch integration issues.

7. **Test Error Propagation** - Add tests for what happens when sub-components fail (LLM errors, file write failures, invalid input).
