"""Unit tests for default trait-based character agent functions."""

import pytest

from agents.character.character_default import (
    _describe_trait,
    _generate_personality_description,
)


class TestDescribeTrait:
    """Tests for the _describe_trait function."""

    @pytest.mark.parametrize(
        "value,expected_level",
        [
            (0, "very low"),
            (10, "very low"),
            (20, "very low"),
            (21, "low"),
            (30, "low"),
            (40, "low"),
            (41, "moderate"),
            (50, "moderate"),
            (60, "moderate"),
            (61, "high"),
            (70, "high"),
            (80, "high"),
            (81, "very high"),
            (90, "very high"),
            (100, "very high"),
        ],
    )
    def test_describe_trait_assertiveness_boundaries(
        self, value: int, expected_level: str
    ):
        """Assertiveness trait correctly maps values to levels."""
        result = _describe_trait("assertiveness", value)

        # Check that the result contains expected descriptions
        if expected_level == "very low":
            assert "passive" in result or "deferential" in result
        elif expected_level == "low":
            assert "yielding" in result
        elif expected_level == "moderate":
            assert "balanced" in result
        elif expected_level == "high":
            assert "confident" in result or "initiative" in result
        elif expected_level == "very high":
            assert "dominant" in result or "forceful" in result

    @pytest.mark.parametrize(
        "value,expected_level",
        [
            (0, "very low"),
            (20, "very low"),
            (21, "low"),
            (40, "low"),
            (41, "moderate"),
            (60, "moderate"),
            (61, "high"),
            (80, "high"),
            (81, "very high"),
            (100, "very high"),
        ],
    )
    def test_describe_trait_warmth_boundaries(self, value: int, expected_level: str):
        """Warmth trait correctly maps values to levels."""
        result = _describe_trait("warmth", value)

        if expected_level == "very low":
            assert "cold" in result or "distant" in result
        elif expected_level == "low":
            assert "reserved" in result
        elif expected_level == "moderate":
            assert "friendly" in result
        elif expected_level == "high":
            assert "warm" in result or "caring" in result
        elif expected_level == "very high":
            assert "nurturing" in result or "extremely warm" in result

    @pytest.mark.parametrize(
        "value,expected_level",
        [
            (0, "very low"),
            (20, "very low"),
            (21, "low"),
            (40, "low"),
            (41, "moderate"),
            (60, "moderate"),
            (61, "high"),
            (80, "high"),
            (81, "very high"),
            (100, "very high"),
        ],
    )
    def test_describe_trait_formality_boundaries(self, value: int, expected_level: str):
        """Formality trait correctly maps values to levels."""
        result = _describe_trait("formality", value)

        if expected_level == "very low":
            assert "casual" in result
        elif expected_level == "low":
            assert "informal" in result
        elif expected_level == "moderate":
            assert "adapts" in result
        elif expected_level == "high":
            assert "formal" in result or "proper" in result
        elif expected_level == "very high":
            assert "very formal" in result or "precise" in result

    @pytest.mark.parametrize(
        "value,expected_level",
        [
            (0, "very low"),
            (20, "very low"),
            (21, "low"),
            (40, "low"),
            (41, "moderate"),
            (60, "moderate"),
            (61, "high"),
            (80, "high"),
            (81, "very high"),
            (100, "very high"),
        ],
    )
    def test_describe_trait_verbosity_boundaries(self, value: int, expected_level: str):
        """Verbosity trait correctly maps values to levels."""
        result = _describe_trait("verbosity", value)

        if expected_level == "very low":
            assert "terse" in result
        elif expected_level == "low":
            assert "concise" in result
        elif expected_level == "moderate":
            assert "balanced" in result
        elif expected_level == "high":
            assert "talkative" in result
        elif expected_level == "very high":
            assert "verbose" in result

    @pytest.mark.parametrize(
        "value,expected_level",
        [
            (0, "very low"),
            (20, "very low"),
            (21, "low"),
            (40, "low"),
            (41, "moderate"),
            (60, "moderate"),
            (61, "high"),
            (80, "high"),
            (81, "very high"),
            (100, "very high"),
        ],
    )
    def test_describe_trait_emotionality_boundaries(
        self, value: int, expected_level: str
    ):
        """Emotionality trait correctly maps values to levels."""
        result = _describe_trait("emotionality", value)

        if expected_level == "very low":
            assert "stoic" in result
        elif expected_level == "low":
            assert "reserved" in result
        elif expected_level == "moderate":
            assert "appropriate" in result
        elif expected_level == "high":
            assert "expressive" in result
        elif expected_level == "very high":
            assert "highly emotional" in result

    def test_describe_trait_unknown_trait_returns_fallback(self):
        """Unknown trait returns a fallback description."""
        result = _describe_trait("unknown_trait", 75)

        # Should return something like "high unknown_trait"
        assert "high" in result
        assert "unknown_trait" in result


class TestGeneratePersonalityDescription:
    """Tests for the _generate_personality_description function."""

    def test_generate_personality_description_all_defaults(
        self, default_trait_properties
    ):
        """All traits at default (50) generate proper descriptions."""
        result = _generate_personality_description(default_trait_properties)

        assert "This character's personality traits:" in result
        assert "Assertiveness" in result
        assert "Warmth" in result
        assert "Formality" in result
        assert "Verbosity" in result
        assert "Emotionality" in result
        # All at 50 should show "(50/100)"
        assert "(50/100)" in result

    def test_generate_personality_description_extreme_low_values(self):
        """All traits at 0 generate 'very low' descriptions."""
        properties = {
            "assertiveness": 0,
            "warmth": 0,
            "formality": 0,
            "verbosity": 0,
            "emotionality": 0,
        }
        result = _generate_personality_description(properties)

        assert "(0/100)" in result
        # Should contain very low indicators for each trait
        assert "passive" in result  # assertiveness
        assert "cold" in result  # warmth
        assert "casual" in result  # formality
        assert "terse" in result  # verbosity
        assert "stoic" in result  # emotionality

    def test_generate_personality_description_extreme_high_values(self):
        """All traits at 100 generate 'very high' descriptions."""
        properties = {
            "assertiveness": 100,
            "warmth": 100,
            "formality": 100,
            "verbosity": 100,
            "emotionality": 100,
        }
        result = _generate_personality_description(properties)

        assert "(100/100)" in result
        # Should contain very high indicators
        assert "dominant" in result  # assertiveness
        assert "extremely warm" in result or "nurturing" in result  # warmth
        assert "very formal" in result  # formality
        assert "verbose" in result  # verbosity
        assert "highly emotional" in result  # emotionality

    def test_generate_personality_description_missing_traits_default_to_50(self):
        """Missing traits default to 50."""
        # Only provide assertiveness
        result = _generate_personality_description({"assertiveness": 90})

        # All traits should still appear
        assert "Assertiveness" in result
        assert "Warmth" in result
        assert "Formality" in result
        assert "Verbosity" in result
        assert "Emotionality" in result
        # Assertiveness should be 90
        assert "(90/100)" in result
        # Others should default to 50
        assert "(50/100)" in result

    def test_generate_personality_description_empty_properties(self):
        """Empty properties dictionary uses all defaults."""
        result = _generate_personality_description({})

        assert "This character's personality traits:" in result
        # All should be at 50/100
        assert result.count("(50/100)") == 5

    def test_generate_personality_description_format(self, default_trait_properties):
        """Output follows expected markdown format."""
        result = _generate_personality_description(default_trait_properties)

        lines = result.split("\n")

        # First line is the header
        assert lines[0] == "This character's personality traits:"

        # Each trait line starts with "- **"
        trait_lines = [line for line in lines[1:] if line.strip()]
        for line in trait_lines:
            assert line.startswith("- **")
            assert "**" in line[3:]  # closing bold
            assert "/100)" in line  # value format
