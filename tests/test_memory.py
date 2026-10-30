from pathlib import Path

from relic.memory import SQLiteMemoryStore


def test_messages_roundtrip_in_order(store: SQLiteMemoryStore) -> None:
    store.add_message("user", "hi", "s1")
    store.add_message("assistant", "yo", "s1")
    msgs = store.recent_messages(10)
    assert [(m.role, m.content, m.session_id) for m in msgs] == [
        ("user", "hi", "s1"),
        ("assistant", "yo", "s1"),
    ]
    assert msgs[0].timestamp


def test_recent_messages_respects_limit(store: SQLiteMemoryStore) -> None:
    for i in range(5):
        store.add_message("user", f"m{i}", "s")
    assert [m.content for m in store.recent_messages(3)] == ["m2", "m3", "m4"]


def test_history_persists_across_connections(tmp_path: Path) -> None:
    db = tmp_path / "x.db"
    first = SQLiteMemoryStore(db)
    first.add_message("user", "remember me", "s1")
    first.close()
    second = SQLiteMemoryStore(db)
    assert [m.content for m in second.recent_messages(5)] == ["remember me"]
    second.close()


def test_facts_add_list_delete(store: SQLiteMemoryStore) -> None:
    a = store.add_fact("likes coffee")
    b = store.add_fact("has a cat")
    assert [f.content for f in store.list_facts()] == ["likes coffee", "has a cat"]
    assert store.delete_fact(a.id) is True
    assert store.delete_fact(a.id) is False
    assert [f.id for f in store.list_facts()] == [b.id]


def test_clear_history_keeps_facts(store: SQLiteMemoryStore) -> None:
    store.add_message("user", "hi", "s")
    store.add_fact("a fact")
    store.clear_history()
    assert store.recent_messages(10) == []
    assert len(store.list_facts()) == 1
