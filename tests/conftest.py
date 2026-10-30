from pathlib import Path

import pytest

from relic.memory import SQLiteMemoryStore
from relic.persona import Persona
from relic.providers import LLMProvider, Message


class FakeProvider(LLMProvider):
    """Records the messages it receives and returns a canned reply."""

    def __init__(self, reply: str = "ok") -> None:
        self.reply = reply
        self.calls: list[list[Message]] = []

    def chat(self, messages: list[Message]) -> str:
        self.calls.append(messages)
        return self.reply


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep the developer's real environment and .env out of tests."""
    for var in (
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "LLM_MODEL",
        "LLM_TEMPERATURE",
        "PERSONA_FILE",
        "USER_NAME",
        "DATA_DIR",
        "HISTORY_LIMIT",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def store(tmp_path: Path):
    s = SQLiteMemoryStore(tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture
def persona() -> Persona:
    return Persona(name="Testy", system_prompt="You are Testy, talking to Sam.")
