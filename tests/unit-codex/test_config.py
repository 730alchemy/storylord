from __future__ import annotations

import os


def test_bootstrap_environment_sets_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "bootstrap")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=from_env_file\n")

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from config import bootstrap_environment, get_settings

    get_settings.cache_clear()
    settings = get_settings()
    bootstrap_environment(settings)

    assert settings.anthropic_api_key == "from_env_file"
    assert os.environ["ANTHROPIC_API_KEY"] == "from_env_file"
