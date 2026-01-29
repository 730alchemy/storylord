"""Unit tests for compute_text_delta in graph/delta.py."""

import difflib

from graph.delta import compute_text_delta


def _expected_deltas(original: str, edited: str) -> list[dict]:
    matcher = difflib.SequenceMatcher(None, original, edited)
    return [
        {"original": original[i1:i2], "edited": edited[j1:j2]}
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def _assert_delta_matches_difflib(original: str, edited: str) -> list[dict]:
    result = compute_text_delta(original, edited)
    assert result == _expected_deltas(original, edited)
    return result


class TestComputeTextDelta:
    """Tests for the compute_text_delta function."""

    def test_identical_texts_returns_empty_list(self):
        """Same text returns empty list."""
        result = _assert_delta_matches_difflib("hello world", "hello world")
        assert result == []

    def test_empty_to_empty_returns_empty_list(self):
        """Empty string to empty string returns empty list."""
        result = _assert_delta_matches_difflib("", "")
        assert result == []

    def test_single_character_replacement(self):
        """Single character replacement is detected."""
        result = _assert_delta_matches_difflib("cat", "bat")

        assert len(result) == 1
        assert result[0]["original"] == "c"
        assert result[0]["edited"] == "b"

    def test_single_word_replacement(self):
        """Word replacement is detected."""
        result = _assert_delta_matches_difflib("hello world", "hello there")

        # Verify changes were detected (difflib may split into multiple chunks)
        assert len(result) >= 1
        combined_original = "".join(d["original"] for d in result)
        combined_edited = "".join(d["edited"] for d in result)
        assert combined_original
        assert combined_edited
        assert combined_original != combined_edited

    def test_insertion_only(self):
        """Insertion of new text is detected."""
        result = _assert_delta_matches_difflib("hello", "hello world")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == " world"

    def test_deletion_only(self):
        """Deletion of text is detected."""
        result = _assert_delta_matches_difflib("hello world", "hello")

        assert len(result) == 1
        assert result[0]["original"] == " world"
        assert result[0]["edited"] == ""

    def test_complete_replacement(self):
        """Complete text replacement is detected."""
        result = _assert_delta_matches_difflib("abc", "xyz")

        assert len(result) == 1
        assert result[0]["original"] == "abc"
        assert result[0]["edited"] == "xyz"

    def test_multiple_changes(self):
        """Multiple disjoint changes are detected."""
        result = _assert_delta_matches_difflib("the quick brown fox", "a quick red fox")

        # Verify multiple changes were detected
        assert len(result) >= 2
        combined_original = "".join(d["original"] for d in result)
        combined_edited = "".join(d["edited"] for d in result)
        assert combined_original
        assert combined_edited
        assert combined_original != combined_edited

    def test_from_empty_string(self):
        """Insertion from empty string."""
        result = _assert_delta_matches_difflib("", "new text")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == "new text"

    def test_to_empty_string(self):
        """Deletion to empty string."""
        result = _assert_delta_matches_difflib("old text", "")

        assert len(result) == 1
        assert result[0]["original"] == "old text"
        assert result[0]["edited"] == ""

    def test_whitespace_change(self):
        """Whitespace changes are detected."""
        result = _assert_delta_matches_difflib("hello world", "hello  world")

        # Difflib detects this as an insertion of a space
        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == " "

    def test_newline_addition(self):
        """Newline changes are detected."""
        result = _assert_delta_matches_difflib("line1line2", "line1\nline2")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == "\n"

    def test_case_change(self):
        """Case changes are detected."""
        result = _assert_delta_matches_difflib("Hello World", "hello world")

        # H -> h and W -> w
        assert len(result) == 2
        changes = [(d["original"], d["edited"]) for d in result]
        assert ("H", "h") in changes
        assert ("W", "w") in changes

    def test_unicode_characters(self):
        """Unicode characters are handled correctly."""
        result = _assert_delta_matches_difflib("hello", "hello 🌍")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == " 🌍"

    def test_unicode_replacement(self):
        """Unicode character replacement works."""
        result = _assert_delta_matches_difflib("hello 🌍", "hello 🌎")

        assert len(result) == 1
        assert result[0]["original"] == "🌍"
        assert result[0]["edited"] == "🌎"

    def test_multiline_text(self):
        """Multiline text changes are detected."""
        original = "line 1\nline 2\nline 3"
        edited = "line 1\nmodified line\nline 3"

        result = _assert_delta_matches_difflib(original, edited)

        assert len(result) >= 1
        combined_original = "".join(d["original"] for d in result)
        combined_edited = "".join(d["edited"] for d in result)
        assert combined_original
        assert combined_edited
        assert combined_original != combined_edited

    def test_preserves_order_of_changes(self):
        """Changes are returned in order of occurrence."""
        result = _assert_delta_matches_difflib("aXbYc", "a1b2c")

        assert len(result) == 2
        assert result[0]["original"] == "X"
        assert result[0]["edited"] == "1"
        assert result[1]["original"] == "Y"
        assert result[1]["edited"] == "2"
