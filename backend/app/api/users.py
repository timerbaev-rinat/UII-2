"""Эндпоинты пользователей.

Основное управление пользователями/ролями реализовано в модуле auth
(/auth/users, /auth/roles). Здесь — просмотр справочных данных о
пользователях для выбора ответственных (без прав администрирования).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.deps import DbSession, Perm, require_permission
from app.models import User
from app.schemas.auth import UserOut

router = APIRouter()


@router.get(
    "",
    response_model=list[UserOut],
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Список пользователей (для выбора ответственных)",
)
async def list_users_for_selection(db: DbSession):
    result = await db.execute(
        select(User).where(User.is_active.is_(True)).order_by(User.full_name)
    )
    return result.scalars().all()