"""Модели справочников: состояния, единицы измерения, материалы.

План предусматривает CRUD справочников (Этап 3): состояния имущества,
единицы измерения, материалы. Выделены в отдельные таблицы для
управляемого справочника (коды + названия).
"""

from __future__ import annotations

import uuid

from sqlalchemy import String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUID_PK, TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class AssetStatus(TimestampMixin, Base):
    """Справочник состояний имущества."""

    __tablename__ = "asset_statuses"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UnitOfMeasure(TimestampMixin, Base):
    """Справочник единиц измерения (шт., кг, м, комплект и т.д.)."""

    __tablename__ = "units_of_measure"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Material(TimestampMixin, Base):
    """Справочник материалов (металл, дерево, пластик и т.д.)."""

    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)