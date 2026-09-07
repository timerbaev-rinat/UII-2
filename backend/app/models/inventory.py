"""Модели инвентаризации: инвентаризации, позиции описи, расхождения."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUID_PK, TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class InventoryStatusEnum(str, enum.Enum):
    """Статусы инвентаризации."""

    DRAFT = "DRAFT"  # создана
    IN_PROGRESS = "IN_PROGRESS"  # в процессе
    COMPLETED = "COMPLETED"  # завершена
    APPROVED = "APPROVED"  # утверждена


class InventoryTypeEnum(str, enum.Enum):
    """Типы инвентаризации."""

    PLANNED = "PLANNED"  # плановая
    UNPLANNED = "UNPLANNED"  # внеплановая
    SAMPLE = "SAMPLE"  # выборочная


class Inventory(TimestampMixin, Base):
    """Инвентаризация."""

    __tablename__ = "inventories"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inv_type: Mapped[InventoryTypeEnum] = mapped_column(
        String(32), default=InventoryTypeEnum.PLANNED.value, nullable=False
    )
    status: Mapped[InventoryStatusEnum] = mapped_column(
        String(32), default=InventoryStatusEnum.DRAFT.value, nullable=False, index=True
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # охват: полная / по подразделениям / по комнатам
    coverage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    commission: Mapped[str | None] = mapped_column(Text, nullable=True)
    building_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("buildings.id"), nullable=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("rooms.id"), nullable=True
    )
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list[InventoryItem]] = relationship(
        back_populates="inventory", cascade="all, delete-orphan"
    )


class InventoryItem(TimestampMixin, Base):
    """Позиция описи: факт, учёт, расхождение, фото."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        # одна позиция на пару «инвентаризация — актив»
        UniqueConstraint("inventory_id", "asset_id", name="uq_inventory_asset"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("inventories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("assets.id"), nullable=False, index=True
    )
    # учётные данные
    accounting_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    accounting_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # фактические данные
    actual_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    actual_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    # фото при инвентаризации
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # отметка о том, что позиция проверена
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=True
    )
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    inventory: Mapped[Inventory] = relationship(back_populates="items")


class DiscrepancyStatusEnum(str, enum.Enum):
    """Статусы расследования расхождения."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class InventoryDiscrepancy(TimestampMixin, Base):
    """Реестр расхождений (недостача/излишек)."""

    __tablename__ = "inventory_discrepancies"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("inventories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("inventory_items.id"), nullable=True
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("assets.id"), nullable=True
    )
    # тип расхождения: недостача (SHORTAGE) / излишек (SURPLUS)
    discrepancy_type: Mapped[str] = mapped_column(String(32), nullable=False)
    accounting_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    actual_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    difference: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[DiscrepancyStatusEnum] = mapped_column(
        String(32), default=DiscrepancyStatusEnum.OPEN.value, nullable=False
    )
    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=True
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("documents.id"), nullable=True
    )