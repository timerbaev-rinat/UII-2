"""Модели пользователей, ролей и разрешений (RBAC).

Включает: users, roles, permissions, user_roles, role_permissions, delegations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUID_PK, TimestampMixin

# Тип первичного ключа (UUID по умолчанию)
def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(TimestampMixin, Base):
    """Пользователь системы."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, primary_key=True, default=_uuid
    )
    login: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list[Role]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )


class Role(TimestampMixin, Base):
    """Роль пользователя."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list[User]] = relationship(
        secondary="user_roles",
        back_populates="roles",
    )
    permissions: Mapped[list[Permission]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )


class Permission(TimestampMixin, Base):
    """Разрешение (действие) в системе."""

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list[Role]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
    )


class UserRole(Base):
    """Связь пользователь ↔ роль (много-ко-многим)."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )


class RolePermission(Base):
    """Матрица «роль — действие»."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class Delegation(TimestampMixin, Base):
    """Временное делегирование полномочий (замещение).

    От кого (delegator), кому (delegatee), на срок (start/end).
    """

    __tablename__ = "delegations"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    delegator_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delegatee_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_code: Mapped[str] = mapped_column(String(64), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)