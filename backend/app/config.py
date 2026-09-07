"""Конфигурация приложения.

Читает переменные окружения из .env (через pydantic-settings).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения.

    Поля соответствуют переменным из .env / docker-compose.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- БД ---
    database_url: str = (
        "postgresql+asyncpg://asset_user:change_me@localhost:5432/asset_school"
    )

    # --- JWT ---
    secret_key: str = "change_me_long_random_secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # --- Сервер ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # --- Файлы ---
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()