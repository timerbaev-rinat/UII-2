"""Модели имущества: типы объектов, атрибуты, карточки, резервирование номеров."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
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


class AssetStatusEnum(str, enum.Enum):
    """Статусы карточки имущества."""

    IN_STOCK = "IN_STOCK"  # на учёте
    MOVED = "MOVED"  # перемещено
    ON_REPAIR = "ON_REPAIR"  # в ремонте
    ISSUED = "ISSUED"  # выдано
    WRITTEN_OFF = "WRITTEN_OFF"  # списано
    RESERVED = "RESERVED"  # зарезервирован номер


class AssetType(TimestampMixin, Base):
    """Справочник типов объектов (оборудование, мебель, спорт, лаб, иное)."""

    __tablename__ = "asset_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # шаблон нумерации, например {Год}-{Тип}-{№}
    number_template: Mapped[str | None] = mapped_column(String(255), nullable=True)

    attributes: Mapped[list[AssetAttribute]] = relationship(
        back_populates="asset_type",
        cascade="all, delete-orphan",
    )
    assets: Mapped[list[Asset]] = relationship(back_populates="asset_type")


class AssetAttribute(TimestampMixin, Base):
    """Настраиваемый атрибут по типу объекта (шаблон карточки)."""

    __tablename__ = "asset_attributes"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    asset_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("asset_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # тип значения: string, number, date, boolean, text
    value_type: Mapped[str] = mapped_column(String(32), default="string", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    asset_type: Mapped[AssetType] = relationship(back_populates="attributes")


class Asset(TimestampMixin, Base):
    """Карточка единицы имущества."""

    __tablename__ = "assets"
    __table_args__ = (
        # Инвентарный номер уникален (среди несписанных)
        UniqueConstraint("inventory_number", name="uq_asset_inventory_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    inventory_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    asset_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("asset_types.id"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("rooms.id"), nullable=True, index=True
    )

    # --- описание ---
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # --- учётные данные ---
    purchase_year: Mapped[int | None] = mapped_column(nullable=True)
    commissioning_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[AssetStatusEnum] = mapped_column(
        String(32), default=AssetStatusEnum.IN_STOCK.value, nullable=False, index=True
    )
    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- количественные ---
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=1, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)  # единица измерения
    material: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- стоимость ---
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    write_off_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- прочее ---
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # JSON с настраиваемыми атрибутами (в Postgres может быть JSONB)
    custom_attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=True
    )

    asset_type: Mapped[AssetType] = relationship(back_populates="assets")
    room: Mapped["Room"] = relationship()  # noqa: F821 (Room в structure.py)

    moves: Mapped[list["AssetMove"]] = relationship(  # noqa: F821
        back_populates="asset", cascade="all, delete-orphan"
    )


class AssetNumberReservation(TimestampMixin, Base):
    """Резервирование инвентарных номеров (авто/ручное присвоение)."""

    __tablename__ = "asset_number_reservations"
    __table_args__ = (
        UniqueConstraint("inventory_number", name="uq_asset_number_reservation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    inventory_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    asset_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("asset_types.id"), nullable=True
    )
    reserved_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK, ForeignKey("assets.id"), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)