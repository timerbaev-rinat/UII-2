"""FastAPI-зависимости: текущий пользователь, проверка разрешений (RBAC).

Включает:
- get_current_user — по access-токену
- require_permission — фабрика зависимостей для проверки permission
- делегирование полномочий учитывается при проверке разрешений
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.database import get_db
from app.models import Delegation, User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    db: DbSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> User:
    """Возвращает текущего пользователя по Bearer-токену."""
    if credentials is None:
        raise _credentials_error()
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise _credentials_error()
        user_id = uuid.UUID(payload.get("sub"))
    except Exception:  # noqa: BLE001
        raise _credentials_error()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _credentials_error()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def _collect_user_permission_codes(db: AsyncSession, user: User) -> set[str]:
    """Собирает коды разрешений пользователя (через роли и делегирования)."""
    codes: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            codes.add(perm.code)
    return codes


async def _collect_delegated_permissions(
    db: AsyncSession, user: User
) -> set[str]:
    """Собирает делегированные пользователю разрешения (активные)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Delegation).where(
            Delegation.delegatee_id == user.id,
            Delegation.is_active.is_(True),
            Delegation.start_at <= now,
            Delegation.end_at >= now,
        )
    )
    return {d.permission_code for d in result.scalars().all()}


def require_permission(permission_code: str):
    """Фабрика зависимости: проверяет наличие permission у пользователя.

    Учитывает разрешения из ролей и активные делегирования.
    """

    async def dependency(user: CurrentUser, db: DbSession) -> User:
        codes = _collect_user_permission_codes(db, user)
        delegated = await _collect_delegated_permissions(db, user)
        codes |= delegated
        if permission_code not in codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: требуется разрешение «{permission_code}»",
            )
        return user

    return dependency


# Константы кодов разрешений (RBAC)
class Perm:
    """Коды разрешений, используемые в require_permission."""

    # карточки
    CREATE_CARD = "create_card"
    EDIT_CARD = "edit_card"
    DELETE_CARD = "delete_card"
    VIEW_CARDS = "view_cards"
    # операции
    MOVE_ASSET = "move_asset"
    APPROVE_WRITEOFF = "approve_writeoff"
    APPROVE_MOVE = "approve_move"
    # инвентаризация
    RUN_INVENTORY = "run_inventory"
    APPROVE_INVENTORY = "approve_inventory"
    # отчёты
    VIEW_REPORTS = "view_reports"
    # администратор
    MANAGE_USERS = "manage_users"
    MANAGE_REFERENCES = "manage_references"
    MANAGE_STRUCTURE = "manage_structure"
    # аудит
    VIEW_AUDIT = "view_audit"