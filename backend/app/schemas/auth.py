"""Pydantic-схемы для модуля аутентификации и пользователей."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Авторизация ---
class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# --- Пользователи ---
class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    login: str
    full_name: str
    position: str | None = None
    is_active: bool
    created_at: datetime
    roles: list[RoleOut] = []


class UserCreate(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)
    position: str | None = None
    password: str = Field(min_length=8, max_length=128)
    role_codes: list[str] = []


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    position: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role_codes: list[str] | None = None


# --- Роли и разрешения ---
class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None


class RoleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    permission_codes: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    permission_codes: list[str] | None = None


class RoleWithPermissions(RoleOut):
    permissions: list[PermissionOut] = []


# --- Делегирование ---
class DelegationCreate(BaseModel):
    delegatee_id: uuid.UUID
    permission_code: str = Field(min_length=1, max_length=64)
    start_at: datetime
    end_at: datetime
    comment: str | None = None


class DelegationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delegator_id: uuid.UUID
    delegatee_id: uuid.UUID
    permission_code: str
    start_at: datetime
    end_at: datetime
    comment: str | None = None
    is_active: bool