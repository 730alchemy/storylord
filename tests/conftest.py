"""Shared test fixtures for storylord tests."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_yaml_path() -> Path:
    """Path to sample input YAML file."""
    return Path(__file__).parent.parent / "examples" / "sample_input.yaml"
