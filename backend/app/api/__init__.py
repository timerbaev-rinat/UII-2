"""Пакет API-роутеров приложения."""

from fastapi import APIRouter

from app.api import auth, health, users, reference, structure, assets, operations, inventory, documents, audit, reports

api_router = APIRouter()

# Подключаем подроутеры
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(reference.router, prefix="/reference", tags=["reference"])
api_router.include_router(structure.router, prefix="/structure", tags=["structure"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(inventory.router, prefix="/inventories", tags=["inventory"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(audit.router, prefix="/audit-log", tags=["audit"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# Агрегирующий роутер для подключения в main
router = api_router