"""Tests for configurable LLM model names."""

from __future__ import annotations


def test_settings_has_llm_default_model(monkeypatch, tmp_path):
    """Settings should have a default model field with the standard value."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=test\n")

    from config import Settings, get_settings

    get_settings.cache_clear()
    s = Settings()
    assert s.llm_default_model == "claude-sonnet-4-20250514"


def test_settings_has_per_agent_model_fields(monkeypatch, tmp_path):
    """Settings should have per-agent model fields that default to None."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=test\n")

    from config import Settings, get_settings

    get_settings.cache_clear()
    s = Settings()
    assert s.llm_character_model is None
    assert s.llm_architect_model is None
    assert s.llm_editor_model is None
    assert s.llm_narrator_model is None


def test_env_var_overrides_default_model(monkeypatch, tmp_path):
    """Environment variable should override the default model."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ANTHROPIC_API_KEY=test\nLLM_DEFAULT_MODEL=custom-model\n"
    )

    from config import Settings, get_settings

    get_settings.cache_clear()
    s = Settings()
    assert s.llm_default_model == "custom-model"


def test_get_model_for_agent_type_returns_default(monkeypatch, tmp_path):
    """get_model_for_agent_type should return default model when no override set."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=test\n")

    from config import get_model_for_agent_type, get_settings

    get_settings.cache_clear()

    model = get_model_for_agent_type("architect")
    assert model == "claude-sonnet-4-20250514"


def test_get_model_for_agent_type_uses_override(monkeypatch, tmp_path):
    """get_model_for_agent_type should use per-agent override when set."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ANTHROPIC_API_KEY=test\nLLM_ARCHITECT_MODEL=architect-model\n"
    )

    from config import get_model_for_agent_type, get_settings

    get_settings.cache_clear()

    assert get_model_for_agent_type("architect") == "architect-model"


def test_get_model_for_agent_type_all_agent_types(monkeypatch, tmp_path):
    """get_model_for_agent_type should work for all agent types."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=test\n")

    from config import get_model_for_agent_type, get_settings

    get_settings.cache_clear()

    # All should return default when no override
    for agent_type in ["character", "architect", "editor", "narrator"]:
        assert get_model_for_agent_type(agent_type) == "claude-sonnet-4-20250514"
