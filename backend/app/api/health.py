"""Health-эндпоинты: проверка работоспособности и подключения к БД."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/ready", summary="Готовность сервиса")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Проверяет, что сервис запущен и БД доступна."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "unavailable"

    status_code = 200 if db_status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if db_status == "ok" else "degraded", "db": db_status},
    )


@router.get("/liveness", summary="Живость процесса")
async def health_liveness():
    """Проверка, что процесс жив (без обращения к БД)."""
    return {"status": "ok"}