import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.database import get_connection


class UserNotFoundError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_user(payload: dict) -> dict:
    user_id = str(uuid4())
    timestamp = _now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (
                id, name, age, sex, height_cm, weight_kg, activity_level, goal,
                dietary_preferences, dietary_restrictions, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload["name"],
                payload.get("age"),
                payload.get("sex"),
                payload.get("height_cm"),
                payload.get("weight_kg"),
                payload.get("activity_level"),
                payload.get("goal"),
                json.dumps(payload.get("dietary_preferences", []), ensure_ascii=False),
                json.dumps(payload.get("dietary_restrictions", []), ensure_ascii=False),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    return get_user(user_id)


def get_user(user_id: str) -> dict:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise UserNotFoundError(user_id)
    return _serialize_user(row)


def update_user(user_id: str, payload: dict) -> dict:
    current = get_user(user_id)
    merged = {
        **current,
        **payload,
    }
    timestamp = _now()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET name = ?, age = ?, sex = ?, height_cm = ?, weight_kg = ?, activity_level = ?,
                goal = ?, dietary_preferences = ?, dietary_restrictions = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                merged["name"],
                merged.get("age"),
                merged.get("sex"),
                merged.get("height_cm"),
                merged.get("weight_kg"),
                merged.get("activity_level"),
                merged.get("goal"),
                json.dumps(merged.get("dietary_preferences", []), ensure_ascii=False),
                json.dumps(merged.get("dietary_restrictions", []), ensure_ascii=False),
                timestamp,
                user_id,
            ),
        )
        connection.commit()
    return get_user(user_id)


def _serialize_user(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "age": row["age"],
        "sex": row["sex"],
        "height_cm": row["height_cm"],
        "weight_kg": row["weight_kg"],
        "activity_level": row["activity_level"],
        "goal": row["goal"],
        "dietary_preferences": json.loads(row["dietary_preferences"] or "[]"),
        "dietary_restrictions": json.loads(row["dietary_restrictions"] or "[]"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
