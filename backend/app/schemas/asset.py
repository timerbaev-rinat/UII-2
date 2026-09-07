"""Pydantic-схемы для карточек имущества и резервирования номеров."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Карточка имущества ---
class AssetCreate(BaseModel):
    asset_type_id: uuid.UUID
    room_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    brand: str | None = Field(default=None, max_length=255)
    serial_number: str | None = Field(default=None, max_length=255)
    purchase_year: int | None = None
    commissioning_date: date | None = None
    warranty_until: date | None = None
    quantity: Decimal = Field(default=Decimal("1"))
    unit: str | None = Field(default=None, max_length=32)
    material: str | None = Field(default=None, max_length=255)
    cost: Decimal | None = None
    description: str | None = None
    photo_path: str | None = None
    custom_attributes: dict | None = None
    responsible_user_id: uuid.UUID | None = None
    # если True — не генерировать номер, а взять вручную
    use_custom_number: bool = False
    inventory_number: str | None = Field(default=None, max_length=64)


class AssetUpdate(BaseModel):
    room_id: uuid.UUID | None = None
    name: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    brand: str | None = Field(default=None, max_length=255)
    serial_number: str | None = Field(default=None, max_length=255)
    purchase_year: int | None = None
    commissioning_date: date | None = None
    warranty_until: date | None = None
    quantity: Decimal | None = None
    unit: str | None = Field(default=None, max_length=32)
    material: str | None = Field(default=None, max_length=255)
    cost: Decimal | None = None
    description: str | None = None
    photo_path: str | None = None
    custom_attributes: dict | None = None
    responsible_user_id: uuid.UUID | None = None
    status: str | None = Field(default=None, max_length=32)


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_number: str
    asset_type_id: uuid.UUID
    room_id: uuid.UUID | None = None
    name: str
    model: str | None = None
    brand: str | None = None
    serial_number: str | None = None
    purchase_year: int | None = None
    commissioning_date: date | None = None
    status: str
    warranty_until: date | None = None
    quantity: Decimal
    unit: str | None = None
    material: str | None = None
    cost: Decimal | None = None
    write_off_date: date | None = None
    description: str | None = None
    photo_path: str | None = None
    custom_attributes: dict | None = None
    responsible_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class AssetListOut(BaseModel):
    """Краткое представление карточки для списков."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_number: str
    name: str
    status: str
    room_id: uuid.UUID | None = None
    asset_type_id: uuid.UUID


# --- Резервирование номеров ---
class ReserveNumberRequest(BaseModel):
    asset_type_id: uuid.UUID
    comment: str | None = None


class ReserveNumberOut(BaseModel):
    inventory_number: str
    reservation_id: uuid.UUID
    expires_at: datetime | None = None


class AssetSearchParams(BaseModel):
    query: str | None = None
    asset_type_id: uuid.UUID | None = None
    room_id: uuid.UUID | None = None
    status: str | None = None
    responsible_user_id: uuid.UUID | None = None