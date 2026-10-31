from pathlib import Path

import pytest

from relic.config import ConfigError, load_settings


def test_defaults_with_only_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "k")
    s = load_settings()
    assert s.llm_base_url == "https://integrate.api.nvidia.com/v1"
    assert s.llm_model == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert s.llm_temperature == 0.8
    assert s.user_name == "choom"
    assert s.persona_file == Path("personas/relic.yaml")
    assert s.data_dir == Path("./data")
    assert s.history_limit == 20


def test_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "llama3")
    monkeypatch.setenv("USER_NAME", "Sam")
    s = load_settings()
    assert s.llm_base_url == "http://localhost:11434/v1"
    assert s.llm_model == "llama3"
    assert s.user_name == "Sam"


def test_reads_dotenv_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("LLM_API_KEY=from-file\nLLM_MODEL=m\n")
    s = load_settings()
    assert s.llm_api_key == "from-file"
    assert s.llm_model == "m"


def test_missing_key_gives_friendly_error() -> None:
    with pytest.raises(ConfigError, match="LLM_API_KEY is not set"):
        load_settings()


def test_invalid_value_gives_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("LLM_TEMPERATURE", "hot")
    with pytest.raises(ConfigError, match="LLM_TEMPERATURE"):
        load_settings()


def test_enable_thinking_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "k")
    assert load_settings().llm_enable_thinking is None
    monkeypatch.setenv("LLM_ENABLE_THINKING", "false")
    assert load_settings().llm_enable_thinking is False
