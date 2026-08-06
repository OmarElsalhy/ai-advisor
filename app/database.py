import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone

from .config import DATABASE_PATH, STORAGE_DIR

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connection() -> sqlite3.Connection:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize() -> None:
    logger.info("Initializing database")
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
            );
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                business_type TEXT NOT NULL,
                language TEXT NOT NULL,
                version TEXT,
                last_reviewed TEXT
            );
            """
        )
    logger.debug("Database tables initialized")


def ensure_session(session_id: str | None, user_id: str | None) -> str:
    with connection() as conn:
        if session_id:
            found = conn.execute("SELECT id FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
            if found:
                logger.debug(f"Session {session_id} found")
                return session_id
        session_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO chat_sessions (id, user_id, created_at) VALUES (?, ?, ?)",
            (session_id, user_id, _now()),
        )
        logger.info(f"New session created: {session_id} for user_id={user_id}")
        return session_id


def add_message(session_id: str, role: str, content: str, sources: list[dict] | None = None) -> None:
    with connection() as conn:
        conn.execute(
            """INSERT INTO chat_messages
            (id, session_id, role, content, sources_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), session_id, role, content, json.dumps(sources or [], ensure_ascii=False), _now()),
        )
    logger.debug(f"Message added to session {session_id}: role={role}")


def get_messages(session_id: str) -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, role, content, sources_json, created_at FROM chat_messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ).fetchall()
    logger.debug(f"Retrieved {len(rows)} messages for session {session_id}")
    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "sources": json.loads(row["sources_json"] or "[]"),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
