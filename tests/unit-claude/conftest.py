"""Shared fixtures for unit tests."""

from __future__ import annotations

import sys

import pytest

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from models import CharacterMemory, CharacterProfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = str(PROJECT_ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture
def empty_memory() -> CharacterMemory:
    """Fresh CharacterMemory with no events."""
    return CharacterMemory()


@pytest.fixture
def sample_profile() -> CharacterProfile:
    """A sample character profile for testing."""
    return CharacterProfile(
        name="Test Character",
        description="A test character for unit testing",
        role="protagonist",
        motivations="Testing the system thoroughly",
        relationships="Works well with other test fixtures",
        backstory="Created in the great test suite of 2024",
    )


@pytest.fixture
def mock_character_agent_type() -> MagicMock:
    """Mock CharacterAgentType for registry tests."""
    mock_type = MagicMock()
    mock_type.name = "mock"
    mock_type.property_schema = {"type": "object", "properties": {}}
    mock_agent = MagicMock()
    mock_agent.memory = CharacterMemory()
    mock_type.create_instance = MagicMock(return_value=mock_agent)
    return mock_type


@pytest.fixture
def mock_tool() -> MagicMock:
    """Mock Tool for registry tests."""
    mock = MagicMock()
    mock.name = "mock_tool"
    mock.description = "A mock tool for testing"
    mock.get_schema.return_value = {"type": "object", "properties": {}}
    mock.execute.return_value = {"result": "success"}
    return mock


@pytest.fixture
def default_trait_properties() -> dict[str, Any]:
    """Default trait properties for character_default tests."""
    return {
        "assertiveness": 50,
        "warmth": 50,
        "formality": 50,
        "verbosity": 50,
        "emotionality": 50,
    }


@pytest.fixture
def default_mbti_properties() -> dict[str, Any]:
    """Default MBTI properties for character_mbti tests."""
    return {
        "extroversion": 50,
        "intuition": 50,
        "thinking": 50,
        "judging": 50,
    }
