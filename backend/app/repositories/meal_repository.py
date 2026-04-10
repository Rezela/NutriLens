import json
from datetime import date, datetime, timezone
from uuid import uuid4

from app.db.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_meal_log(payload: dict) -> dict:
    meal_id = str(uuid4())
    timestamp = _now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO meals (
                id, user_id, image_path, meal_name, description, estimated_calories,
                protein_g, carbs_g, fat_g, confidence, health_flags, follow_up_questions,
                reasoning_summary, items_json, raw_model_output, source_notes, meal_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meal_id,
                payload.get("user_id"),
                payload.get("image_path"),
                payload["meal_name"],
                payload.get("description"),
                payload["estimated_calories"],
                payload["protein_g"],
                payload["carbs_g"],
                payload["fat_g"],
                payload.get("confidence"),
                json.dumps(payload.get("health_flags", []), ensure_ascii=False),
                json.dumps(payload.get("follow_up_questions", []), ensure_ascii=False),
                payload.get("reasoning_summary"),
                json.dumps(payload.get("items", []), ensure_ascii=False),
                json.dumps(payload.get("raw_model_output", {}), ensure_ascii=False),
                payload.get("source_notes"),
                payload.get("meal_time") or timestamp,
                timestamp,
            ),
        )
        connection.commit()
    return get_meal_by_id(meal_id)


def get_meal_by_id(meal_id: str) -> dict:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM meals WHERE id = ?", (meal_id,)).fetchone()
    if row is None:
        raise ValueError(f"Meal not found: {meal_id}")
    return _serialize_meal(row)


def list_meals(user_id: str | None = None) -> list[dict]:
    query = "SELECT * FROM meals"
    params: tuple = ()
    if user_id:
        query += " WHERE user_id = ?"
        params = (user_id,)
    query += " ORDER BY meal_time DESC, created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_serialize_meal(row) for row in rows]


def get_daily_stats(user_id: str, target_date: date) -> dict:
    date_prefix = target_date.isoformat()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(estimated_calories), 0) AS total_calories,
                COALESCE(SUM(protein_g), 0) AS total_protein_g,
                COALESCE(SUM(carbs_g), 0) AS total_carbs_g,
                COALESCE(SUM(fat_g), 0) AS total_fat_g,
                COUNT(*) AS meal_count
            FROM meals
            WHERE user_id = ? AND substr(meal_time, 1, 10) = ?
            """,
            (user_id, date_prefix),
        ).fetchone()
    return {
        "user_id": user_id,
        "date": date_prefix,
        "total_calories": row["total_calories"],
        "total_protein_g": row["total_protein_g"],
        "total_carbs_g": row["total_carbs_g"],
        "total_fat_g": row["total_fat_g"],
        "meal_count": row["meal_count"],
    }


def _serialize_meal(row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "image_path": row["image_path"],
        "meal_name": row["meal_name"],
        "description": row["description"],
        "estimated_calories": row["estimated_calories"],
        "protein_g": row["protein_g"],
        "carbs_g": row["carbs_g"],
        "fat_g": row["fat_g"],
        "confidence": row["confidence"],
        "health_flags": json.loads(row["health_flags"] or "[]"),
        "follow_up_questions": json.loads(row["follow_up_questions"] or "[]"),
        "reasoning_summary": row["reasoning_summary"],
        "items": json.loads(row["items_json"] or "[]"),
        "source_notes": row["source_notes"],
        "meal_time": row["meal_time"],
        "created_at": row["created_at"],
    }
