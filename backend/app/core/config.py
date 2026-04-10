from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NutriLens Backend"
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    database_url: str = "sqlite:///./storage/nutrilens.db"
    upload_dir: str = "storage/uploads"
    memory_dir: str = "storage/memory"
    memory_recent_meal_limit: int = 20
    allowed_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value or value.strip() == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def database_path(self) -> Path:
        raw = self.database_url.replace("sqlite:///", "", 1)
        return Path(raw)

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def memory_path(self) -> Path:
        return Path(self.memory_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
