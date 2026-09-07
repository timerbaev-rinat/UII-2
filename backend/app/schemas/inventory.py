"""Pydantic-схемы для инвентаризации."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Инвентаризация ---
class InventoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    inv_type: str = Field(default="PLANNED", max_length=32)
    start_date: date | None = None
    end_date: date | None = None
    coverage: str | None = Field(default=None, max_length=64)
    commission: str | None = None
    building_id: uuid.UUID | None = None
    room_id: uuid.UUID | None = None
    department: str | None = Field(default=None, max_length=255)


class InventoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    inv_type: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=32)
    start_date: date | None = None
    end_date: date | None = None
    coverage: str | None = Field(default=None, max_length=64)
    commission: str | None = None
    department: str | None = Field(default=None, max_length=255)


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    inv_type: str
    status: str
    start_date: date | None = None
    end_date: date | None = None
    coverage: str | None = None
    commission: str | None = None
    building_id: uuid.UUID | None = None
    room_id: uuid.UUID | None = None
    department: str | None = None
    created_by_id: uuid.UUID
    approved_by_id: uuid.UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime


class InventoryApproveRequest(BaseModel):
    comment: str | None = None


# --- Позиции описи ---
class InventoryItemUpdate(BaseModel):
    """Обновление фактических данных позиции (мобильный сценарий)."""
    actual_quantity: Decimal | None = None
    actual_status: str | None = Field(default=None, max_length=32)
    actual_condition: str | None = None
    photo_path: str | None = None
    is_checked: bool | None = None
    comment: str | None = None


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_id: uuid.UUID
    asset_id: uuid.UUID
    accounting_quantity: Decimal | None = None
    accounting_status: str | None = None
    actual_quantity: Decimal | None = None
    actual_status: str | None = None
    actual_condition: str | None = None
    photo_path: str | None = None
    is_checked: bool
    checked_by_id: uuid.UUID | None = None
    checked_at: datetime | None = None
    comment: str | None = None


# --- Расхождения ---
class DiscrepancyUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=32)
    responsible_user_id: uuid.UUID | None = None
    explanation: str | None = None
    resolution: str | None = None


class DiscrepancyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_id: uuid.UUID
    inventory_item_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    discrepancy_type: str
    accounting_quantity: Decimal | None = None
    actual_quantity: Decimal | None = None
    difference: Decimal | None = None
    estimated_cost: Decimal | None = None
    status: str
    responsible_user_id: uuid.UUID | None = None
    explanation: str | None = None
    resolution: str | None = None
    document_id: uuid.UUID | None = None