"""Memory storage: an interface plus a SQLite implementation.

`MemoryStore` is deliberately small so a vector database (e.g. Chroma) can
replace or extend `SQLiteMemoryStore` later without touching the agent.
"""

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class StoredMessage:
    """One persisted chat message."""

    role: str
    content: str
    timestamp: str
    session_id: str


@dataclass(frozen=True)
class Fact:
    """A long-term fact the user asked Relic to remember."""

    id: int
    content: str
    created_at: str


class MemoryStore(ABC):
    """Interface for conversation history and long-term facts."""

    @abstractmethod
    def add_message(self, role: str, content: str, session_id: str) -> None:
        """Persist a chat message."""

    @abstractmethod
    def recent_messages(self, limit: int) -> list[StoredMessage]:
        """Return the last `limit` messages, oldest first."""

    @abstractmethod
    def clear_history(self) -> None:
        """Delete all stored messages (facts are kept)."""

    @abstractmethod
    def add_fact(self, content: str) -> Fact:
        """Save a long-term fact."""

    @abstractmethod
    def list_facts(self) -> list[Fact]:
        """Return all facts, oldest first."""

    @abstractmethod
    def delete_fact(self, fact_id: int) -> bool:
        """Delete a fact by id. Returns False if it did not exist."""

    def close(self) -> None:  # noqa: B027 - optional hook
        """Release any resources."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class SQLiteMemoryStore(MemoryStore):
    """SQLite-backed store using only the standard library."""

    def __init__(self, db_path: Path | str) -> None:
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL
            )"""
        )
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        self._conn.commit()

    def add_message(self, role: str, content: str, session_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO messages (role, content, timestamp, session_id) VALUES (?, ?, ?, ?)",
                (role, content, _now(), session_id),
            )

    def recent_messages(self, limit: int) -> list[StoredMessage]:
        rows = self._conn.execute(
            "SELECT role, content, timestamp, session_id FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [StoredMessage(*row) for row in reversed(rows)]

    def clear_history(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM messages")

    def add_fact(self, content: str) -> Fact:
        created = _now()
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO facts (content, created_at) VALUES (?, ?)", (content, created)
            )
        return Fact(id=int(cur.lastrowid or 0), content=content, created_at=created)

    def list_facts(self) -> list[Fact]:
        rows = self._conn.execute(
            "SELECT id, content, created_at FROM facts ORDER BY id"
        ).fetchall()
        return [Fact(*row) for row in rows]

    def delete_fact(self, fact_id: int) -> bool:
        with self._conn:
            cur = self._conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
        return cur.rowcount > 0

    def close(self) -> None:
        self._conn.close()
