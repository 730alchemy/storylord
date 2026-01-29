# Unit Test Analysis (tests/unit-claude)

## Fragility
- `tests/unit-claude/agents/character/test_character_default.py` and `tests/unit-claude/agents/character/test_character_mbti.py` assert specific wording ("Strongly introverted", "dominant", etc.), so copy edits will break tests even if behavior is unchanged.
- `tests/unit-claude/test_models.py` checks literal summary strings from `CharacterMemory.get_summary`; any formatting tweak (bullets, labels, ellipsis rules) will fail.
- `tests/unit-claude/graph/test_delta.py` depends on `difflib.SequenceMatcher` chunking; a different delta strategy (or minor algorithm change) would fail tests though the delta still represents the same edit.

## Duplication
- Discovery tests in `tests/unit-claude/agents/test_discovery.py` repeat the same patterns for architects/narrators/editors/character types; this could be parameterized.
- Trait/MBTI boundary tests repeat similar logic in `tests/unit-claude/agents/character/test_character_default.py` and `tests/unit-claude/agents/character/test_character_mbti.py`.
- `sample_profile` fixture is duplicated in `tests/unit-claude/agents/character/test_registry.py` and `tests/unit-claude/conftest.py`.

## Gaps
- No tests for shared-mutable-default safety in `CharacterMemory`, `RelationshipState`, etc. (`src/models.py` uses list/dict defaults).
- No tests for "short content" summaries (non-truncated event text still gets an ellipsis), or for the "No significant memories yet." branch in `CharacterMemory.get_summary`.
- `CharacterRegistry` behavior on duplicate `character_id` isn’t tested (overwrite vs. error), and `restore_memories` isn’t tested for mixed existing+missing IDs.
- `CharacterSpeakTool` tests don’t validate that extra kwargs are truly ignored (they only assert that a “dialogue” key exists).
- Discovery functions are tested for sorting but not for empty list results on every category.

## Correctness / Weak Assertions
- `tests/unit-claude/graph/test_delta.py::test_single_word_replacement` would pass even if the delta omitted the deletion (it only checks absence of words in concatenations).
- `tests/unit-claude/graph/test_delta.py::test_multiple_changes` is very loose (checks only “the/brown” or “a/red”), so partial or incorrect deltas can still pass.
- `tests/unit-claude/graph/test_delta.py::test_multiline_text` allows “modified” *or* “line 2”, so incomplete deltas could still pass.

## Suggestions
- Strengthen delta tests: add a helper that applies `compute_text_delta` to the original and asserts it reconstructs the edited string (content + order).
- Soften brittle text checks: assert structural markers (headers, labels, counts) and key tokens rather than full phrases, or switch to snapshot tests if wording is meant to be stable.
- Parametrize discovery and trait/dimension tests to cut duplication and make new categories easier to add.
- Add edge-case tests: mutable defaults isolation in `CharacterMemory`, duplicate character IDs in `CharacterRegistry`, short-content summary formatting, and ignored kwargs in `CharacterSpeakTool`.
