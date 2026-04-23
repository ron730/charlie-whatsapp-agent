import sqlite3
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH, MAX_HISTORY


def _connect() -> sqlite3.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                id_message TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL
            )
        """)


def is_processed(id_message: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_messages WHERE id_message = ?", (id_message,)
        ).fetchone()
        return row is not None


def mark_processed(id_message: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_messages (id_message, processed_at) VALUES (?, ?)",
            (id_message, datetime.utcnow().isoformat()),
        )


def append(chat_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO conversations (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, datetime.utcnow().isoformat()),
        )


def tail(chat_id: str, n: int = MAX_HISTORY) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM conversations
            WHERE chat_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (chat_id, n),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
