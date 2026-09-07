"""Модели операций с имуществом: перемещения, списания, ремонт, выдача/возврат."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUID_PK, DocumentStatusMixin, TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class AssetMove(TimestampMixin, Base):
    """Перемещение имущества (из комнаты в комнату)."""

    __tablename__ = "asset_moves"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("rooms.id"), nullable=True
    )
    to_room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("rooms.id"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    moved_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("documents.id"), nullable=True
    )

    asset: Mapped["Asset"] = relationship(back_populates="moves")  # noqa: F821


class WriteOff(DocumentStatusMixin, TimestampMixin, Base):
    """Списание имущества (комиссия, документы, согласование)."""

    __tablename__ = "write_offs"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    commission_members: Mapped[str | None] = mapped_column(Text, nullable=True)
    write_off_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("documents.id"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )


class Repair(TimestampMixin, Base):
    """Ремонт/обслуживание имущества."""

    __tablename__ = "repairs"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contractor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_guarantee: Mapped[bool] = mapped_column(default=False, nullable=False)
    act_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("documents.id"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )


class Issuance(TimestampMixin, Base):
    """Выдача/возврат имущества (для уроков/мероприятий)."""

    __tablename__ = "issuances"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    issued_to_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    issued_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_return: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # состояние при возврате
    returned_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_returned: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )