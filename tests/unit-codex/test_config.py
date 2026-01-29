from __future__ import annotations

import os


def test_initialize_environment_sets_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "bootstrap")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=from_env_file\n")

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    import config as config_module

    settings = config_module.initialize_environment()

    assert settings.anthropic_api_key == "from_env_file"
    assert os.environ["ANTHROPIC_API_KEY"] == "from_env_file"


def test_configure_logging_creates_logs_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    import config as config_module

    config_module.configure_logging()

    assert (tmp_path / "logs").exists()
