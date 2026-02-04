"""Unit tests for character_store slugify_name function."""

from __future__ import annotations

import pytest

from character_store.slugify import slugify_name


class TestSlugifyName:
    """Tests for the slugify_name function."""

    def test_given_simple_two_word_name_when_slugified_then_lowercase_hyphenated(self):
        """Simple two-word name becomes lowercase hyphenated slug."""
        assert slugify_name("Elijah Boondog") == "elijah-boondog"

    def test_given_name_with_special_characters_when_slugified_then_only_alphanumeric_and_hyphens(
        self,
    ):
        """Special characters are stripped, leaving only alphanumeric and hyphens."""
        result = slugify_name("O'Brien & Sons!")
        assert all(c.isalnum() or c == "-" for c in result)
        assert "'" not in result
        assert "&" not in result
        assert "!" not in result

    def test_given_name_with_leading_trailing_spaces_when_slugified_then_no_leading_trailing_hyphens(
        self,
    ):
        """Leading and trailing spaces do not produce leading or trailing hyphens."""
        result = slugify_name("  Elijah Boondog  ")
        assert not result.startswith("-")
        assert not result.endswith("-")
        assert result == "elijah-boondog"

    def test_given_name_with_multiple_consecutive_spaces_when_slugified_then_single_hyphen(
        self,
    ):
        """Multiple consecutive spaces collapse to a single hyphen."""
        result = slugify_name("Elijah   Boondog")
        assert "--" not in result
        assert result == "elijah-boondog"

    def test_given_name_with_periods_and_hyphens_like_dr_smith_jones_iii_when_slugified_then_clean_slug(
        self,
    ):
        """Complex name with periods, hyphens, and roman numerals produces a clean slug."""
        result = slugify_name("Dr. Smith-Jones III")
        assert not result.startswith("-")
        assert not result.endswith("-")
        assert "--" not in result
        assert all(c.isalnum() or c == "-" for c in result)

    def test_given_single_word_name_when_slugified_then_lowercase_no_hyphens(self):
        """Single word name becomes lowercase with no hyphens."""
        assert slugify_name("Jasper") == "jasper"

    def test_given_name_with_unicode_characters_when_slugified_then_transliterated_to_ascii(
        self,
    ):
        """Unicode characters are transliterated to ASCII equivalents."""
        result = slugify_name("José García")
        assert result.isascii()
        assert "jose" in result
        assert "garcia" in result

    def test_given_empty_string_when_slugified_then_raises_ValueError(self):
        """Empty string input raises ValueError."""
        with pytest.raises(ValueError, match="[Ee]mpty"):
            slugify_name("")
