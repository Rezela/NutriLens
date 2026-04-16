from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NutriLens Backend"
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    gemini_model: str = "gemini-1.5-flash"
    google_cloud_project: str = ""
    google_cloud_location: str = "global"
    google_application_credentials: str = ""
    database_url: str = "sqlite:///./storage/nutrilens.db"
    upload_dir: str = "storage/uploads"
    memory_dir: str = "storage/memory"
    memory_recent_meal_limit: int = 20
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

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

    @property
    def google_application_credentials_path(self) -> Path | None:
        if not self.google_application_credentials:
            return None
        return Path(self.google_application_credentials)

    @property
    def allowed_origins_list(self) -> list[str]:
        if not self.allowed_origins or self.allowed_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
