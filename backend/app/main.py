"""Точка входа FastAPI-приложения.

Собирает приложение, подключает CORS, middleware безопасности/логирования,
обработчик ошибок и роутеры.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app import api
from app.config import settings
from app.core.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    setup_logging,
)
from app.database import Base, engine

logger = logging.getLogger("app.main")

# Настройка логов при импорте модуля
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения.

    При старте создаются таблицы, если их нет (для разработки).
    В продакшене миграции выполняются через Alembic (см. docker-compose).
    """
    # В development создаём таблицы автоматически.
    # В Docker (production) перед запуском выполняется `alembic upgrade head`,
    # поэтому здесь это безопасно (таблицы уже есть).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Учёт имущества школы",
    description=(
        "Строгий учёт имущества школы для муниципалитета: карточки, "
        "инвентаризация, отчёты, аудит."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# --- Middleware (внешние добавляются последними) ---
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# CORS (для локальной разработки фронта отдельно от бэкенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(api.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик: логирует причину, клиенту отдаёт общее сообщение."""
    logger.exception(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )


@app.get("/", tags=["health"])
async def root():
    return {
        "app": "Учёт имущества школы",
        "version": "0.1.0",
        "docs": "/docs",
    }