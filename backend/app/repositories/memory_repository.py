from datetime import datetime, timezone
from uuid import uuid4

from app.db.database import get_connection


class MemoryNotFoundError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_memories(user_id: str, active_only: bool = True) -> list[dict]:
    query = "SELECT * FROM memories WHERE user_id = ?"
    params: list = [user_id]
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY memory_type ASC, updated_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return [_serialize_memory(row) for row in rows]


def get_memory(memory_id: str) -> dict:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row is None:
        raise MemoryNotFoundError(memory_id)
    return _serialize_memory(row)


def upsert_memory(payload: dict) -> dict:
    timestamp = _now()
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM memories WHERE user_id = ? AND memory_type = ? AND slug = ?",
            (payload["user_id"], payload["memory_type"], payload["slug"]),
        ).fetchone()
        if existing:
            memory_id = existing["id"]
            connection.execute(
                """
                UPDATE memories
                SET title = ?, summary = ?, details = ?, source_kind = ?, confidence = ?, is_active = 1, updated_at = ?
                WHERE id = ?
                """,
                (
                    payload["title"],
                    payload["summary"],
                    payload.get("details"),
                    payload.get("source_kind"),
                    payload.get("confidence"),
                    timestamp,
                    memory_id,
                ),
            )
        else:
            memory_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO memories (
                    id, user_id, memory_type, slug, title, summary, details,
                    source_kind, confidence, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    memory_id,
                    payload["user_id"],
                    payload["memory_type"],
                    payload["slug"],
                    payload["title"],
                    payload["summary"],
                    payload.get("details"),
                    payload.get("source_kind"),
                    payload.get("confidence"),
                    timestamp,
                    timestamp,
                ),
            )
        connection.commit()
    return get_memory(memory_id)


def archive_memory(user_id: str, memory_type: str, slug: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE memories SET is_active = 0, updated_at = ? WHERE user_id = ? AND memory_type = ? AND slug = ?",
            (_now(), user_id, memory_type, slug),
        )
        connection.commit()


def _serialize_memory(row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "memory_type": row["memory_type"],
        "slug": row["slug"],
        "title": row["title"],
        "summary": row["summary"],
        "details": row["details"],
        "source_kind": row["source_kind"],
        "confidence": row["confidence"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
