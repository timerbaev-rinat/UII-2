"""Pydantic-схемы для карточек имущества (Этап 4)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    inventory_number: str = Field(min_length=1, max_length=64)
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
    custom_attributes: dict | None = None
    responsible_user_id: uuid.UUID | None = None


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
    custom_attributes: dict | None = None
    responsible_user_id: uuid.UUID | None = None


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


class ReserveNumberRequest(BaseModel):
    asset_type_id: uuid.UUID | None = None
    count: int = Field(default=1, ge=1, le=100)
    comment: str | None = None


class ReserveNumberOut(BaseModel):
    inventory_number: str
    reservation_id: uuid.UUID


class MoveCreate(BaseModel):
    to_room_id: uuid.UUID
    from_room_id: uuid.UUID | None = None
    reason: str | None = None
    document_id: uuid.UUID | None = None


class OperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    created_at: datetime


class AssetNumberGenerateRequest(BaseModel):
    asset_type_code: str = Field(min_length=1, max_length=64)
    count: int = Field(default=1, ge=1, le=100)