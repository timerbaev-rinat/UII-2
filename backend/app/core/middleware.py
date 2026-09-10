"""HTTP-middleware и настройка логирования.

- SecurityHeadersMiddleware — добавляет заголовки безопасности (CSP,
  X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS, no-store).
- RequestLoggingMiddleware — структурированное логирование запросов.
- setup_logging() — единая настройка логгеров (в stderr).
"""

from __future__ import annotations

import logging
import sys
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

logger = logging.getLogger("app.access")


def _build_csp() -> str:
    """Собирает Content-Security-Policy.

    Базовый набор совместим с Vuetify/Vite. В `strict_csp` ужесточаем
    script-src (без inline). Отключение политики — `security_headers=False`.
    """
    base = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "object-src 'none'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "media-src 'self' blob:; "
    )
    if settings.strict_csp:
        return base + "script-src 'self'; style-src 'self'"
    # dev/дефолт: разрешаем inline (Vuetify стили, сборка Vite)
    return base + "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Добавляет защитные HTTP-заголовки к каждому ответу."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        response = await call_next(request)
        if not settings.security_headers:
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(self), microphone=(), usb=()"
        )
        if settings.hsts_enabled:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        csp = _build_csp()
        if csp:
            response.headers["Content-Security-Policy"] = csp

        # Ответы API не кешируем (чувствительные данные, токены)
        if request.url.path.startswith("/auth") or request.url.path.startswith("/assets"):
            response.headers["Cache-Control"] = "no-store"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Логирует каждый HTTP-запрос с методом, путём, статусом и временем."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request method=%s path=%s status=%d duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def setup_logging() -> None:
    """Настраивает логирование приложения в stderr."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=handlers,
        force=True,
    )
    # Тихие сторонние логгеры
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)