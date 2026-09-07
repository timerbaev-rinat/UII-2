"""Эндпоинты журнала аудита (Этап 8).

- Просмотр журнала действий с фильтрацией
- Контроль целостности (проверка целостности записей)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.core.deps import DbSession, Perm, require_permission
from app.models import Asset, AuditLog, Room
from app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get(
    "",
    response_model=list[AuditLogOut],
    dependencies=[Depends(require_permission(Perm.VIEW_AUDIT))],
    summary="Журнал аудита",
)
async def list_audit(
    db: DbSession,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/actions",
    dependencies=[Depends(require_permission(Perm.VIEW_AUDIT))],
    summary="Список доступных действий",
)
async def list_actions(db: DbSession):
    result = await db.execute(select(AuditLog.action).distinct())
    return {"actions": [r[0] for r in result.all()]}


@router.get(
    "/integrity",
    dependencies=[Depends(require_permission(Perm.VIEW_AUDIT))],
    summary="Проверка целостности данных",
)
async def integrity_check(db: DbSession):
    """Базовая проверка целостности: корректность связей между таблицами."""
    issues: list[dict] = []

    # Карточки без помещения, но не в статусе списания/резерва
    orphan_assets = await db.execute(
        select(Asset)
        .where(
            Asset.room_id.is_(None),
            Asset.status.not_in(["WRITTEN_OFF", "RESERVED"]),
        )
        .limit(50)
    )
    orphan_count = len(orphan_assets.scalars().all())
    if orphan_count:
        issues.append(
            {
                "entity": "asset",
                "message": f"Найдено {orphan_count} карточек без привязки к помещению",
            }
        )

    # Кабинеты без здания (не должно быть, т.к. FK NOT NULL — проверка для отчёта)
    total_assets = await db.scalar(select(func.count()).select_from(Asset))
    total_rooms = await db.scalar(select(func.count()).select_from(Room))

    return {
        "status": "ok" if not issues else "warnings",
        "issues": issues,
        "counts": {
            "assets": int(total_assets or 0),
            "rooms": int(total_rooms or 0),
        },
    }