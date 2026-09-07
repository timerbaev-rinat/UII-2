"""Эндпоинты аутентификации и управления пользователями/ролями (RBAC).

- POST /auth/login, /auth/refresh, /auth/change-password
- CRUD пользователей, ролей, разрешений
- Делегирование полномочий
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    CurrentUser,
    DbSession,
    Perm,
    require_permission,
)
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import (
    Delegation,
    Permission,
    Role,
    User,
    UserRole,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    DelegationCreate,
    DelegationOut,
    LoginRequest,
    PermissionOut,
    RefreshRequest,
    RoleCreate,
    RoleOut,
    RoleUpdate,
    RoleWithPermissions,
    TokenPair,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


# --- Авторизация ---
@router.post("/login", response_model=TokenPair, summary="Вход")
async def login(
    payload: LoginRequest,
    db: DbSession,
    request: Request,
):
    result = await db.execute(select(User).where(User.login == payload.login))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Учётная запись деактивирована")

    await write_audit(
        db,
        user_id=user.id,
        action="LOGIN",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=_get_client_ip(request),
    )
    await db.commit()

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenPair, summary="Обновление токена")
async def refresh(payload: RefreshRequest, db: DbSession):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != REFRESH_TOKEN_TYPE:
            raise ValueError
        user_id = uuid.UUID(data.get("sub"))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Невалидный refresh-токен")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не активен")

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/change-password", summary="Смена пароля")
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser,
    db: DbSession,
    request: Request,
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
    user.password_hash = hash_password(payload.new_password)
    await write_audit(
        db,
        user_id=user.id,
        action="CHANGE_PASSWORD",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    return {"detail": "Пароль изменён"}


@router.get("/me", response_model=UserOut, summary="Текущий пользователь")
async def me(user: CurrentUser):
    return user


# --- Пользователи (администрирование) ---
@router.get(
    "/users",
    response_model=list[UserOut],
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Список пользователей",
)
async def list_users(db: DbSession):
    result = await db.execute(select(User).order_by(User.full_name))
    return result.scalars().all()


@router.post(
    "/users",
    response_model=UserOut,
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Создание пользователя",
)
async def create_user(payload: UserCreate, db: DbSession):
    exists = await db.execute(select(User).where(User.login == payload.login))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Логин уже занят")

    user = User(
        login=payload.login,
        full_name=payload.full_name,
        position=payload.position,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    await _sync_user_roles(db, user, payload.role_codes)
    await db.commit()
    await db.refresh(user)
    return user


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Пользователь по id",
)
async def get_user(user_id: uuid.UUID, db: DbSession):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.patch(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Обновление пользователя",
)
async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: DbSession):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.position is not None:
        user.position = payload.position
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.role_codes is not None:
        await _sync_user_roles(db, user, payload.role_codes)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Удаление пользователя",
)
async def delete_user(user_id: uuid.UUID, db: DbSession):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await db.delete(user)
    await db.commit()
    return {"detail": "Пользователь удалён"}


# --- Роли ---
@router.get(
    "/roles",
    response_model=list[RoleWithPermissions],
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Список ролей",
)
async def list_roles(db: DbSession):
    result = await db.execute(select(Role).order_by(Role.name))
    return result.scalars().all()


@router.post(
    "/roles",
    response_model=RoleOut,
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Создание роли",
)
async def create_role(payload: RoleCreate, db: DbSession):
    exists = await db.execute(select(Role).where(Role.code == payload.code))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Роль с таким кодом уже есть")
    role = Role(code=payload.code, name=payload.name, description=payload.description)
    db.add(role)
    await db.flush()
    await _sync_role_permissions(db, role, payload.permission_codes)
    await db.commit()
    await db.refresh(role)
    return role


@router.patch(
    "/roles/{role_id}",
    response_model=RoleWithPermissions,
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Обновление роли",
)
async def update_role(role_id: uuid.UUID, payload: RoleUpdate, db: DbSession):
    role = await db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.permission_codes is not None:
        await _sync_role_permissions(db, role, payload.permission_codes)
    await db.commit()
    await db.refresh(role)
    return role


# --- Разрешения ---
@router.get(
    "/permissions",
    response_model=list[PermissionOut],
    dependencies=[Depends(require_permission(Perm.MANAGE_USERS))],
    summary="Список разрешений",
)
async def list_permissions(db: DbSession):
    result = await db.execute(select(Permission).order_by(Permission.code))
    return result.scalars().all()


# --- Делегирование ---
@router.post(
    "/delegations",
    response_model=DelegationOut,
    summary="Делегировать полномочие",
)
async def create_delegation(payload: DelegationCreate, user: CurrentUser, db: DbSession):
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="end_at должен быть позже start_at")
    delegation = Delegation(
        delegator_id=user.id,
        delegatee_id=payload.delegatee_id,
        permission_code=payload.permission_code,
        start_at=payload.start_at,
        end_at=payload.end_at,
        comment=payload.comment,
        is_active=True,
    )
    db.add(delegation)
    await db.commit()
    await db.refresh(delegation)
    return delegation


@router.get(
    "/delegations",
    response_model=list[DelegationOut],
    summary="Мои делегирования",
)
async def list_delegations(user: CurrentUser, db: DbSession):
    result = await db.execute(
        select(Delegation)
        .where(
            (Delegation.delegator_id == user.id)
            | (Delegation.delegatee_id == user.id)
        )
        .order_by(Delegation.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/delegations/{delegation_id}/revoke",
    response_model=DelegationOut,
    summary="Отозвать делегирование",
)
async def revoke_delegation(
    delegation_id: uuid.UUID, user: CurrentUser, db: DbSession
):
    delegation = await db.get(Delegation, delegation_id)
    if delegation is None:
        raise HTTPException(status_code=404, detail="Делегирование не найдено")
    if delegation.delegator_id != user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    delegation.is_active = False
    await db.commit()
    await db.refresh(delegation)
    return delegation


# --- Вспомогательные функции ---
async def _sync_user_roles(db: AsyncSession, user: User, role_codes: list[str]) -> None:
    """Обновляет роли пользователя по кодам."""
    await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user.id))
    if role_codes:
        result = await db.execute(select(Role).where(Role.code.in_(role_codes)))
        for role in result.scalars().all():
            db.add(UserRole(user_id=user.id, role_id=role.id))


async def _sync_role_permissions(
    db: AsyncSession, role: Role, permission_codes: list[str]
) -> None:
    """Обновляет разрешения роли по кодам."""
    from app.models import RolePermission

    await db.execute(
        RolePermission.__table__.delete().where(RolePermission.role_id == role.id)
    )
    if permission_codes:
        result = await db.execute(
            select(Permission).where(Permission.code.in_(permission_codes))
        )
        for perm in result.scalars().all():
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))