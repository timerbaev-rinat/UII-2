"""Базовые классы и миксины для моделей.

Содержит общие типы полей, миксин временных меток и миксин
статусной модели документа (черновик → согласование → утверждено).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Тип для первичного ключа (UUID)
UUID_PK = UUID(as_uuid=True)


class DocumentStatusEnum(str, enum.Enum):
    """Статусы документов и операций."""

    DRAFT = "DRAFT"  # черновик
    ON_APPROVAL = "ON_APPROVAL"  # на согласовании
    APPROVED = "APPROVED"  # утверждено


class TimestampMixin:
    """Добавляет поля created_at и updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DocumentStatusMixin:
    """Добавляет статус документа, а также кто и когда изменил статус.

    После перехода в APPROVED редактирование/удаление запрещается.
    """

    status: Mapped[DocumentStatusEnum] = mapped_column(
        String(32),
        default=DocumentStatusEnum.DRAFT.value,
        nullable=False,
    )
    status_changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )