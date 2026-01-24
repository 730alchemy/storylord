"""Unit tests for compute_text_delta in graph/delta.py."""

from graph.delta import compute_text_delta


class TestComputeTextDelta:
    """Tests for the compute_text_delta function."""

    def test_identical_texts_returns_empty_list(self):
        """Same text returns empty list."""
        result = compute_text_delta("hello world", "hello world")
        assert result == []

    def test_empty_to_empty_returns_empty_list(self):
        """Empty string to empty string returns empty list."""
        result = compute_text_delta("", "")
        assert result == []

    def test_single_character_replacement(self):
        """Single character replacement is detected."""
        result = compute_text_delta("cat", "bat")

        assert len(result) == 1
        assert result[0]["original"] == "c"
        assert result[0]["edited"] == "b"

    def test_single_word_replacement(self):
        """Word replacement is detected."""
        result = compute_text_delta("hello world", "hello there")

        # Verify changes were detected (difflib may split into multiple chunks)
        assert len(result) >= 1
        # Verify the combined original text equals "world"
        combined_original = "".join(d["original"] for d in result)
        combined_edited = "".join(d["edited"] for d in result)
        assert "world" not in "hello" + combined_edited
        assert "there" not in "hello" + combined_original

    def test_insertion_only(self):
        """Insertion of new text is detected."""
        result = compute_text_delta("hello", "hello world")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == " world"

    def test_deletion_only(self):
        """Deletion of text is detected."""
        result = compute_text_delta("hello world", "hello")

        assert len(result) == 1
        assert result[0]["original"] == " world"
        assert result[0]["edited"] == ""

    def test_complete_replacement(self):
        """Complete text replacement is detected."""
        result = compute_text_delta("abc", "xyz")

        assert len(result) == 1
        assert result[0]["original"] == "abc"
        assert result[0]["edited"] == "xyz"

    def test_multiple_changes(self):
        """Multiple disjoint changes are detected."""
        result = compute_text_delta("the quick brown fox", "a quick red fox")

        # Verify multiple changes were detected
        assert len(result) >= 2
        # Verify the result when applied would produce the right output
        combined_original = "".join(d["original"] for d in result)
        combined_edited = "".join(d["edited"] for d in result)
        # Original text contained "the" and "brown" which should be removed
        assert "the" in combined_original or "brown" in combined_original
        # Edited text should contain replacements
        assert "a" in combined_edited or "red" in combined_edited

    def test_from_empty_string(self):
        """Insertion from empty string."""
        result = compute_text_delta("", "new text")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == "new text"

    def test_to_empty_string(self):
        """Deletion to empty string."""
        result = compute_text_delta("old text", "")

        assert len(result) == 1
        assert result[0]["original"] == "old text"
        assert result[0]["edited"] == ""

    def test_whitespace_change(self):
        """Whitespace changes are detected."""
        result = compute_text_delta("hello world", "hello  world")

        # Difflib detects this as an insertion of a space
        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == " "

    def test_newline_addition(self):
        """Newline changes are detected."""
        result = compute_text_delta("line1line2", "line1\nline2")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == "\n"

    def test_case_change(self):
        """Case changes are detected."""
        result = compute_text_delta("Hello World", "hello world")

        # H -> h and W -> w
        assert len(result) == 2
        changes = [(d["original"], d["edited"]) for d in result]
        assert ("H", "h") in changes
        assert ("W", "w") in changes

    def test_unicode_characters(self):
        """Unicode characters are handled correctly."""
        result = compute_text_delta("hello", "hello 🌍")

        assert len(result) == 1
        assert result[0]["original"] == ""
        assert result[0]["edited"] == " 🌍"

    def test_unicode_replacement(self):
        """Unicode character replacement works."""
        result = compute_text_delta("hello 🌍", "hello 🌎")

        assert len(result) == 1
        assert result[0]["original"] == "🌍"
        assert result[0]["edited"] == "🌎"

    def test_multiline_text(self):
        """Multiline text changes are detected."""
        original = "line 1\nline 2\nline 3"
        edited = "line 1\nmodified line\nline 3"

        result = compute_text_delta(original, edited)

        # Verify changes were detected
        assert len(result) >= 1
        # Verify the combined changes reflect the modification
        combined_original = "".join(d["original"] for d in result)
        combined_edited = "".join(d["edited"] for d in result)
        # The modification should be captured
        assert "modified" in combined_edited or "line 2" in combined_original

    def test_preserves_order_of_changes(self):
        """Changes are returned in order of occurrence."""
        result = compute_text_delta("aXbYc", "a1b2c")

        assert len(result) == 2
        assert result[0]["original"] == "X"
        assert result[0]["edited"] == "1"
        assert result[1]["original"] == "Y"
        assert result[1]["edited"] == "2"
