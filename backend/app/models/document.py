"""Модели документов: акты, приложения, подписи, версии."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUID_PK, DocumentStatusMixin, TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Document(DocumentStatusMixin, TimestampMixin, Base):
    """Документ (акт приёма-передачи, акт списания, приложение)."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    doc_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)  # тип документа
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # подписи
    signer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=True
    )
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signer_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    # привязка к операциям (опционально)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("assets.id"), nullable=True
    )
    inventory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("inventories.id"), nullable=True
    )
    write_off_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("write_offs.id"), nullable=True
    )
    repair_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("repairs.id"), nullable=True
    )