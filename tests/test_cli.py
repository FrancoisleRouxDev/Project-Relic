import io

from rich.console import Console

from conftest import FakeProvider
from relic.agent import Agent
from relic.cli import handle_command, run_chat
from relic.memory import SQLiteMemoryStore
from relic.persona import Persona


def make(persona: Persona, store: SQLiteMemoryStore) -> tuple[Agent, Console, io.StringIO]:
    out = io.StringIO()
    console = Console(file=out, force_terminal=False, width=100)
    return Agent(FakeProvider("yo"), persona, store, "Sam"), console, out


def test_remember_facts_forget(persona: Persona, store: SQLiteMemoryStore) -> None:
    agent, console, out = make(persona, store)
    assert handle_command("/remember likes tea", agent, console)
    assert [f.content for f in store.list_facts()] == ["likes tea"]
    handle_command("/facts", agent, console)
    assert "likes tea" in out.getvalue()
    handle_command("/forget 1", agent, console)
    assert store.list_facts() == []


def test_exit_stops_loop(persona: Persona, store: SQLiteMemoryStore) -> None:
    agent, console, _ = make(persona, store)
    assert handle_command("/exit", agent, console) is False


def test_chat_loop_replies_then_exits(
    persona: Persona, store: SQLiteMemoryStore, monkeypatch
) -> None:
    agent, console, out = make(persona, store)
    inputs = iter(["hello", "/exit"])
    monkeypatch.setattr(console, "input", lambda _prompt="": next(inputs))
    run_chat(agent, console)
    assert "Testy: yo" in out.getvalue()
