from __future__ import annotations

from typing import Any

import pytest

from agents.character.character_default import (
    DefaultCharacterAgentType,
    _describe_trait,
    _generate_personality_description,
)
from agents.character.character_mbti import (
    MBTICharacterAgentType,
    _describe_ei_dimension,
    _describe_jp_dimension,
    _describe_ns_dimension,
    _describe_tf_dimension,
    _get_mbti_type,
)
from models import CharacterProfile


class DummyLLM:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.model = kwargs.get("model")

    def with_structured_output(self, *_args: Any, **_kwargs: Any) -> "DummyLLM":
        return self

    def bind_tools(self, *_args: Any, **_kwargs: Any) -> "DummyLLM":
        return self


@pytest.fixture
def character_profile() -> CharacterProfile:
    return CharacterProfile(
        name="Test",
        description="Desc",
        role="protagonist",
        motivations="Motivation",
        relationships="None",
        backstory="Backstory",
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        (20, "passive, deferential, avoids confrontation"),
        (40, "generally yielding, prefers others to lead"),
        (60, "balanced, assertive when needed but flexible"),
        (80, "confident, takes initiative, speaks their mind"),
        (81, "dominant, forceful, commands attention"),
    ],
)
def test_describe_trait_boundaries(value: int, expected: str) -> None:
    assert _describe_trait("assertiveness", value) == expected


def test_generate_personality_description_defaults():
    text = _generate_personality_description({})
    assert "This character's personality traits" in text
    assert "Assertiveness" in text
    assert "50/100" in text


def test_get_mbti_type_thresholds():
    assert _get_mbti_type({}) == "ENTJ"
    assert (
        _get_mbti_type(
            {"extroversion": 49, "intuition": 49, "thinking": 49, "judging": 49}
        )
        == "ISFP"
    )


@pytest.mark.parametrize(
    "func,value,expected_prefix",
    [
        (_describe_ei_dimension, 25, "Strongly introverted"),
        (_describe_ei_dimension, 45, "Introverted"),
        (_describe_ei_dimension, 55, "Balanced"),
        (_describe_ei_dimension, 75, "Extroverted"),
        (_describe_ei_dimension, 76, "Strongly extroverted"),
        (_describe_ns_dimension, 25, "Strongly sensing"),
        (_describe_ns_dimension, 45, "Sensing preference"),
        (_describe_ns_dimension, 55, "Balanced"),
        (_describe_ns_dimension, 75, "Intuitive"),
        (_describe_ns_dimension, 76, "Strongly intuitive"),
        (_describe_tf_dimension, 25, "Strongly feeling"),
        (_describe_tf_dimension, 45, "Feeling preference"),
        (_describe_tf_dimension, 55, "Balanced"),
        (_describe_tf_dimension, 75, "Thinking preference"),
        (_describe_tf_dimension, 76, "Strongly thinking"),
        (_describe_jp_dimension, 25, "Strongly perceiving"),
        (_describe_jp_dimension, 45, "Perceiving preference"),
        (_describe_jp_dimension, 55, "Balanced"),
        (_describe_jp_dimension, 75, "Judging preference"),
        (_describe_jp_dimension, 76, "Strongly judging"),
    ],
)
def test_mbti_dimension_boundaries(func, value: int, expected_prefix: str) -> None:
    assert func(value).startswith(expected_prefix)


def test_default_character_agent_type_applies_defaults(
    monkeypatch: pytest.MonkeyPatch, character_profile: CharacterProfile
) -> None:
    monkeypatch.setattr("agents.character.base.ChatAnthropic", DummyLLM)

    agent = DefaultCharacterAgentType().create_instance(
        character_id="c1",
        character_profile=character_profile,
        type_properties={},
        instructions="",
    )

    assert agent.properties == {
        "assertiveness": 50,
        "warmth": 50,
        "formality": 50,
        "verbosity": 50,
        "emotionality": 50,
    }


def test_mbti_character_agent_type_applies_defaults(
    monkeypatch: pytest.MonkeyPatch, character_profile: CharacterProfile
) -> None:
    monkeypatch.setattr("agents.character.base.ChatAnthropic", DummyLLM)

    agent = MBTICharacterAgentType().create_instance(
        character_id="c2",
        character_profile=character_profile,
        type_properties={},
        instructions="",
    )

    assert agent.properties == {
        "extroversion": 50,
        "intuition": 50,
        "thinking": 50,
        "judging": 50,
    }
    assert agent.mbti_type == "ENTJ"
