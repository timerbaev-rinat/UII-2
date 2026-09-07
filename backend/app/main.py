"""Точка входа FastAPI-приложения.

Собирает приложение, подключает CORS, роутеры и обрабатывает
запуск/остановку (проверка БД при старте).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import api
from app.config import settings
from app.database import Base, engine


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


@app.get("/", tags=["health"])
async def root():
    return {
        "app": "Учёт имущества школы",
        "version": "0.1.0",
        "docs": "/docs",
    }