import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.config import get_settings


def ensure_storage() -> None:
    settings = get_settings()
    db_path = settings.database_path
    upload_path = settings.upload_path
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    ensure_storage()
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                sex TEXT,
                height_cm REAL,
                weight_kg REAL,
                activity_level TEXT,
                goal TEXT,
                dietary_preferences TEXT NOT NULL,
                dietary_restrictions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meals (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                image_path TEXT,
                meal_name TEXT NOT NULL,
                description TEXT,
                estimated_calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbs_g REAL NOT NULL,
                fat_g REAL NOT NULL,
                confidence TEXT,
                health_flags TEXT NOT NULL,
                follow_up_questions TEXT NOT NULL,
                reasoning_summary TEXT,
                items_json TEXT NOT NULL,
                raw_model_output TEXT NOT NULL,
                source_notes TEXT,
                meal_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    connection = sqlite3.connect(settings.database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
