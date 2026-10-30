from conftest import FakeProvider
from relic.agent import Agent
from relic.memory import SQLiteMemoryStore
from relic.persona import Persona


def make_agent(provider, persona: Persona, store: SQLiteMemoryStore, limit: int = 20) -> Agent:
    return Agent(provider, persona, store, user_name="Sam", history_limit=limit)


def test_prompt_order_persona_facts_history(persona: Persona, store: SQLiteMemoryStore) -> None:
    store.add_fact("likes coffee")
    store.add_message("user", "earlier question", "old")
    store.add_message("assistant", "earlier answer", "old")
    agent = make_agent(FakeProvider(), persona, store)
    store.add_message("user", "new question", agent.session_id)

    msgs = agent.build_messages()

    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    system = msgs[0]["content"]
    assert system.startswith("You are Testy")
    assert "## Things you know about Sam\n- likes coffee" in system
    assert system.index("You are Testy") < system.index("likes coffee")
    assert [m["content"] for m in msgs[1:]] == [
        "earlier question",
        "earlier answer",
        "new question",
    ]


def test_no_facts_section_when_empty(persona: Persona, store: SQLiteMemoryStore) -> None:
    agent = make_agent(FakeProvider(), persona, store)
    assert agent.system_prompt() == persona.system_prompt


def test_history_is_limited(persona: Persona, store: SQLiteMemoryStore) -> None:
    for i in range(6):
        store.add_message("user", f"m{i}", "s")
    msgs = make_agent(FakeProvider(), persona, store, limit=2).build_messages()
    assert [m["content"] for m in msgs[1:]] == ["m4", "m5"]


def test_respond_persists_both_sides_and_sends_user_message(
    persona: Persona, store: SQLiteMemoryStore
) -> None:
    provider = FakeProvider(reply="hello back")
    agent = make_agent(provider, persona, store)
    assert agent.respond("hello") == "hello back"
    assert provider.calls[0][-1] == {"role": "user", "content": "hello"}
    assert [(m.role, m.content) for m in store.recent_messages(10)] == [
        ("user", "hello"),
        ("assistant", "hello back"),
    ]
