"""Модели структуры учреждения: здания и кабинеты/помещения."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUID_PK, TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Building(TimestampMixin, Base):
    """Здание (корпус) учреждения."""

    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    building_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    rooms: Mapped[list[Room]] = relationship(
        back_populates="building", cascade="all, delete-orphan"
    )


class Room(TimestampMixin, Base):
    """Кабинет/помещение."""

    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    # тип помещения: кабинет / склад / столовая / спортзал / иное
    room_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    building: Mapped[Building] = relationship(back_populates="rooms")