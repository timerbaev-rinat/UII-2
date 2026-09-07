"""Модель журнала действий (аудит)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUID_PK


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class AuditLog(Base):
    """Журнал действий пользователей.

    Фиксирует: кто, когда, действие, сущность, поле, старое/новое значение, IP.
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # действие: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, STATUS_CHANGE, ...
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # сущность: asset, room, write_off, inventory, ...
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )