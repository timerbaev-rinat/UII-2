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
    secret_key: str = "change_me_long_random_secret_0123456789abcdef"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # --- Сервер ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # --- Среда выполнения / безопасность HTTP ---
    env: str = "development"  # development | production
    # Refresh-токен в HttpOnly-куке (дополнительно к телу ответа). По умолчанию выкл.
    cookie_name: str = "refresh_token"
    cookie_httponly: bool = True
    cookie_secure: bool = False  # включать только при HTTPS
    cookie_samesite: str = "lax"
    # Заголовки безопасности (CSP, X-Frame-Options и пр.)
    security_headers: bool = True
    # Строгий CSP (для продакшена). В dev может мешать HMR/инструментам.
    strict_csp: bool = False
    # HSTS включается только при HTTPS за обратным прокси
    hsts_enabled: bool = False
    # Разрешённые хосты (TrustedHostMiddleware), "*" — любые
    allowed_hosts: str = "*"
    # Уровень логирования
    log_level: str = "INFO"

    # --- Файлы ---
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        if self.allowed_hosts.strip() == "*":
            return ["*"]
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()