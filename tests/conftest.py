"""Global pytest configuration for test imports."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(PROJECT_ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture
def sample_yaml_path() -> Path:
    """Path to the sample YAML used by TUI tests."""
    path = PROJECT_ROOT / "examples" / "sample_input.yaml"
    if not path.exists():
        pytest.skip(f"Missing sample YAML fixture at {path}")
    return path
