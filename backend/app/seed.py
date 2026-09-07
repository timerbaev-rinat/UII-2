"""Bootstrap начальных данных: роли, разрешения, администратор.

Запуск:  python -m app.seed
Идемпотентный: повторный запуск безопасен (проверка существования по коду).
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import Perm
from app.core.security import hash_password
from app.database import Base, async_session_maker, engine
from app.models import Permission, Role, User

# Коды ролей
ROLE_ADMIN = "ADMIN"
ROLE_ZAVHOZ = "ZAVHOZ"
ROLE_DIRECTOR = "DIRECTOR"
ROLE_MUNICIPALITY = "MUNICIPALITY"
ROLE_INSPECTOR = "INSPECTOR"

# Все коды разрешений из класса Perm
ALL_PERMISSIONS = [
    Perm.CREATE_CARD,
    Perm.EDIT_CARD,
    Perm.DELETE_CARD,
    Perm.VIEW_CARDS,
    Perm.MOVE_ASSET,
    Perm.APPROVE_WRITEOFF,
    Perm.APPROVE_MOVE,
    Perm.RUN_INVENTORY,
    Perm.APPROVE_INVENTORY,
    Perm.VIEW_REPORTS,
    Perm.MANAGE_USERS,
    Perm.MANAGE_REFERENCES,
    Perm.MANAGE_STRUCTURE,
    Perm.VIEW_AUDIT,
]

# Матрица ролей → разрешения
ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_ADMIN: ALL_PERMISSIONS,
    ROLE_ZAVHOZ: [
        Perm.CREATE_CARD,
        Perm.EDIT_CARD,
        Perm.DELETE_CARD,
        Perm.VIEW_CARDS,
        Perm.MOVE_ASSET,
        Perm.APPROVE_WRITEOFF,
        Perm.APPROVE_MOVE,
        Perm.RUN_INVENTORY,
        Perm.APPROVE_INVENTORY,
        Perm.MANAGE_REFERENCES,
        Perm.MANAGE_STRUCTURE,
    ],
    ROLE_DIRECTOR: [
        Perm.VIEW_CARDS,
        Perm.VIEW_REPORTS,
        Perm.VIEW_AUDIT,
        Perm.APPROVE_WRITEOFF,
        Perm.APPROVE_INVENTORY,
        Perm.APPROVE_MOVE,
    ],
    ROLE_MUNICIPALITY: [
        Perm.VIEW_CARDS,
        Perm.VIEW_REPORTS,
        Perm.VIEW_AUDIT,
    ],
    ROLE_INSPECTOR: [
        Perm.VIEW_CARDS,
        Perm.RUN_INVENTORY,
        Perm.VIEW_REPORTS,
    ],
}

ROLE_NAMES = {
    ROLE_ADMIN: "Администратор",
    ROLE_ZAVHOZ: "Завхоз",
    ROLE_DIRECTOR: "Директор",
    ROLE_MUNICIPALITY: "Муниципалитет",
    ROLE_INSPECTOR: "Инспектор",
}

# Начальный администратор (создаётся, если пользователей нет)
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "Администратор системы"


async def _create_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Создаёт все разрешения, возвращает словарь код → объект."""
    perms: dict[str, Permission] = {}
    for code in ALL_PERMISSIONS:
        existing = await db.execute(select(Permission).where(Permission.code == code))
        perm = existing.scalar_one_or_none()
        if perm is None:
            perm = Permission(code=code, name=code, description=f"Разрешение {code}")
            db.add(perm)
            await db.flush()
        perms[code] = perm
    return perms


async def _create_roles(
    db: AsyncSession, perms: dict[str, Permission]
) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for code, name in ROLE_NAMES.items():
        existing = await db.execute(select(Role).where(Role.code == code))
        role = existing.scalar_one_or_none()
        if role is None:
            role = Role(code=code, name=name, description=f"Роль «{name}»")
            db.add(role)
            await db.flush()
        roles[code] = role

    # Синхронизируем permissions ролей
    for code, perm_codes in ROLE_PERMISSIONS.items():
        role = roles[code]
        role.permissions = [perms[pc] for pc in perm_codes]

    return roles


async def _create_admin(db: AsyncSession, roles: dict[str, Role]) -> None:
    """Создаёт администратора, если пользователей нет вообще."""
    count = await db.scalar(select(User.id).limit(1))
    if count is not None:
        return
    admin = User(
        login=ADMIN_LOGIN,
        full_name=ADMIN_FULL_NAME,
        position="Администратор",
        password_hash=hash_password(ADMIN_PASSWORD),
        is_active=True,
        roles=[roles[ROLE_ADMIN]],
    )
    db.add(admin)


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        perms = await _create_permissions(db)
        roles = await _create_roles(db, perms)
        await _create_admin(db, roles)
        await db.commit()

    print("Seed завершён: роли и разрешения созданы, администратор готов.")


if __name__ == "__main__":
    asyncio.run(main())