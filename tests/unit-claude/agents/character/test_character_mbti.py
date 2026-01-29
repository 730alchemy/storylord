"""Unit tests for MBTI-based character agent functions."""

import pytest

from agents.character.character_mbti import (
    _get_mbti_type,
    _describe_ei_dimension,
    _describe_ns_dimension,
    _describe_tf_dimension,
    _describe_jp_dimension,
    _generate_personality_description,
)


class TestGetMBTIType:
    """Tests for the _get_mbti_type function."""

    @pytest.mark.parametrize(
        "props,expected",
        [
            # All high values (>= 50) -> ENTJ
            (
                {
                    "extroversion": 100,
                    "intuition": 100,
                    "thinking": 100,
                    "judging": 100,
                },
                "ENTJ",
            ),
            # All low values (< 50) -> ISFP
            (
                {"extroversion": 0, "intuition": 0, "thinking": 0, "judging": 0},
                "ISFP",
            ),
            # Exactly 50 -> E/N/T/J (>= 50)
            (
                {"extroversion": 50, "intuition": 50, "thinking": 50, "judging": 50},
                "ENTJ",
            ),
            # Exactly 49 -> I/S/F/P (< 50)
            (
                {"extroversion": 49, "intuition": 49, "thinking": 49, "judging": 49},
                "ISFP",
            ),
            # Empty props default to 50 -> ENTJ
            ({}, "ENTJ"),
        ],
    )
    def test_get_mbti_type_boundary_cases(self, props: dict, expected: str):
        """MBTI type is correctly derived at boundary values."""
        assert _get_mbti_type(props) == expected

    @pytest.mark.parametrize(
        "props,expected",
        [
            # INTJ
            (
                {"extroversion": 0, "intuition": 100, "thinking": 100, "judging": 100},
                "INTJ",
            ),
            # INTP
            (
                {"extroversion": 0, "intuition": 100, "thinking": 100, "judging": 0},
                "INTP",
            ),
            # ENTJ
            (
                {
                    "extroversion": 100,
                    "intuition": 100,
                    "thinking": 100,
                    "judging": 100,
                },
                "ENTJ",
            ),
            # ENTP
            (
                {"extroversion": 100, "intuition": 100, "thinking": 100, "judging": 0},
                "ENTP",
            ),
            # INFJ
            (
                {"extroversion": 0, "intuition": 100, "thinking": 0, "judging": 100},
                "INFJ",
            ),
            # INFP
            (
                {"extroversion": 0, "intuition": 100, "thinking": 0, "judging": 0},
                "INFP",
            ),
            # ENFJ
            (
                {"extroversion": 100, "intuition": 100, "thinking": 0, "judging": 100},
                "ENFJ",
            ),
            # ENFP
            (
                {"extroversion": 100, "intuition": 100, "thinking": 0, "judging": 0},
                "ENFP",
            ),
            # ISTJ
            (
                {"extroversion": 0, "intuition": 0, "thinking": 100, "judging": 100},
                "ISTJ",
            ),
            # ISTP
            (
                {"extroversion": 0, "intuition": 0, "thinking": 100, "judging": 0},
                "ISTP",
            ),
            # ESTJ
            (
                {"extroversion": 100, "intuition": 0, "thinking": 100, "judging": 100},
                "ESTJ",
            ),
            # ESTP
            (
                {"extroversion": 100, "intuition": 0, "thinking": 100, "judging": 0},
                "ESTP",
            ),
            # ISFJ
            (
                {"extroversion": 0, "intuition": 0, "thinking": 0, "judging": 100},
                "ISFJ",
            ),
            # ISFP
            (
                {"extroversion": 0, "intuition": 0, "thinking": 0, "judging": 0},
                "ISFP",
            ),
            # ESFJ
            (
                {"extroversion": 100, "intuition": 0, "thinking": 0, "judging": 100},
                "ESFJ",
            ),
            # ESFP
            (
                {"extroversion": 100, "intuition": 0, "thinking": 0, "judging": 0},
                "ESFP",
            ),
        ],
    )
    def test_get_mbti_type_all_16_types(self, props: dict, expected: str):
        """All 16 MBTI types can be generated."""
        assert _get_mbti_type(props) == expected

    def test_get_mbti_type_partial_props_use_defaults(self):
        """Missing properties default to 50."""
        # Only extroversion is low, rest default to 50 -> I, N, T, J
        result = _get_mbti_type({"extroversion": 0})
        assert result == "INTJ"


class TestDescribeEIDimension:
    """Tests for the _describe_ei_dimension function."""

    @pytest.mark.parametrize(
        "value,expected_keyword",
        [
            (0, "introverted"),
            (25, "introverted"),
            (26, "introverted"),
            (45, "introverted"),
            (46, "balanced"),
            (50, "balanced"),
            (55, "balanced"),
            (56, "extroverted"),
            (75, "extroverted"),
            (76, "extroverted"),
            (100, "extroverted"),
        ],
    )
    def test_describe_ei_boundaries(self, value: int, expected_keyword: str):
        """E/I dimension description matches expected boundaries."""
        result = _describe_ei_dimension(value)
        assert expected_keyword in result.lower()

    def test_describe_ei_strongly_introverted_content(self):
        """Strongly introverted description has expected content."""
        result = _describe_ei_dimension(0)
        assert "reflective" in result
        assert "alone time" in result

    def test_describe_ei_strongly_extroverted_content(self):
        """Strongly extroverted description has expected content."""
        result = _describe_ei_dimension(100)
        assert "social" in result
        assert "outgoing" in result


class TestDescribeNSDimension:
    """Tests for the _describe_ns_dimension function."""

    @pytest.mark.parametrize(
        "value,expected_keyword",
        [
            (0, "sensing"),
            (25, "sensing"),
            (26, "sensing"),
            (45, "sensing"),
            (46, "balanced"),
            (55, "balanced"),
            (56, "intuitive"),
            (75, "intuitive"),
            (76, "intuitive"),
            (100, "intuitive"),
        ],
    )
    def test_describe_ns_boundaries(self, value: int, expected_keyword: str):
        """N/S dimension description matches expected boundaries."""
        result = _describe_ns_dimension(value)
        assert expected_keyword in result.lower()

    def test_describe_ns_strongly_sensing_content(self):
        """Strongly sensing description has expected content."""
        result = _describe_ns_dimension(0)
        assert "concrete" in result or "practical" in result

    def test_describe_ns_strongly_intuitive_content(self):
        """Strongly intuitive description has expected content."""
        result = _describe_ns_dimension(100)
        assert "connections" in result or "innovation" in result


class TestDescribeTFDimension:
    """Tests for the _describe_tf_dimension function."""

    @pytest.mark.parametrize(
        "value,expected_keyword",
        [
            (0, "feeling"),
            (25, "feeling"),
            (26, "feeling"),
            (45, "feeling"),
            (46, "balanced"),
            (55, "balanced"),
            (56, "thinking"),
            (75, "thinking"),
            (76, "thinking"),
            (100, "thinking"),
        ],
    )
    def test_describe_tf_boundaries(self, value: int, expected_keyword: str):
        """T/F dimension description matches expected boundaries."""
        result = _describe_tf_dimension(value)
        assert expected_keyword in result.lower()

    def test_describe_tf_strongly_feeling_content(self):
        """Strongly feeling description has expected content."""
        result = _describe_tf_dimension(0)
        assert "values" in result or "empathetic" in result

    def test_describe_tf_strongly_thinking_content(self):
        """Strongly thinking description has expected content."""
        result = _describe_tf_dimension(100)
        assert "analytical" in result or "logic" in result


class TestDescribeJPDimension:
    """Tests for the _describe_jp_dimension function."""

    @pytest.mark.parametrize(
        "value,expected_keyword",
        [
            (0, "perceiving"),
            (25, "perceiving"),
            (26, "perceiving"),
            (45, "perceiving"),
            (46, "balanced"),
            (55, "balanced"),
            (56, "judging"),
            (75, "judging"),
            (76, "judging"),
            (100, "judging"),
        ],
    )
    def test_describe_jp_boundaries(self, value: int, expected_keyword: str):
        """J/P dimension description matches expected boundaries."""
        result = _describe_jp_dimension(value)
        assert expected_keyword in result.lower()

    def test_describe_jp_strongly_perceiving_content(self):
        """Strongly perceiving description has expected content."""
        result = _describe_jp_dimension(0)
        assert "spontaneous" in result or "adaptable" in result

    def test_describe_jp_strongly_judging_content(self):
        """Strongly judging description has expected content."""
        result = _describe_jp_dimension(100)
        assert "organized" in result or "methodical" in result


class TestGenerateMBTIPersonalityDescription:
    """Tests for the _generate_personality_description function."""

    def test_generate_personality_description_contains_mbti_type(
        self, default_mbti_properties
    ):
        """Output contains the derived MBTI type."""
        result = _generate_personality_description(default_mbti_properties)
        # Default values (all 50) -> ENTJ
        assert "ENTJ" in result

    def test_generate_personality_description_all_dimensions_described(
        self, default_mbti_properties
    ):
        """All four dimensions are described."""
        result = _generate_personality_description(default_mbti_properties)

        assert "Extroversion/Introversion" in result
        assert "Intuition/Sensing" in result
        assert "Thinking/Feeling" in result
        assert "Judging/Perceiving" in result

    def test_generate_personality_description_shows_values(
        self, default_mbti_properties
    ):
        """Output shows dimension values."""
        result = _generate_personality_description(default_mbti_properties)

        # All at 50
        assert "(50/100)" in result

    def test_generate_personality_description_empty_props_uses_defaults(self):
        """Empty properties use defaults of 50."""
        result = _generate_personality_description({})

        # Should be ENTJ (all >= 50)
        assert "ENTJ" in result
        # All values should be 50
        assert result.count("(50/100)") == 4

    def test_generate_personality_description_intj(self):
        """INTJ type generates correct description."""
        props = {
            "extroversion": 0,
            "intuition": 100,
            "thinking": 100,
            "judging": 100,
        }
        result = _generate_personality_description(props)

        assert "INTJ" in result
        assert "Strongly introverted" in result
        assert "Strongly intuitive" in result
        assert "Strongly thinking" in result
        assert "Strongly judging" in result

    def test_generate_personality_description_isfp(self):
        """ISFP type generates correct description."""
        props = {
            "extroversion": 0,
            "intuition": 0,
            "thinking": 0,
            "judging": 0,
        }
        result = _generate_personality_description(props)

        assert "ISFP" in result
        assert "Strongly introverted" in result
        assert "Strongly sensing" in result
        assert "Strongly feeling" in result
        assert "Strongly perceiving" in result

    def test_generate_personality_description_format(self, default_mbti_properties):
        """Output follows expected format."""
        result = _generate_personality_description(default_mbti_properties)

        # Should start with the MBTI type header
        assert result.startswith("This character has an **")
        assert "** personality type based on their MBTI dimensions:" in result

        # Should have section headers
        assert "**Extroversion/Introversion**" in result
        assert "**Intuition/Sensing**" in result
        assert "**Thinking/Feeling**" in result
        assert "**Judging/Perceiving**" in result
