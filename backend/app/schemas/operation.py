"""Pydantic-схемы для операций с имуществом: перемещения, списания, ремонт, выдача."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Перемещение ---
class AssetMoveCreate(BaseModel):
    asset_id: uuid.UUID
    to_room_id: uuid.UUID | None = None
    reason: str | None = None


class AssetMoveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    from_room_id: uuid.UUID | None = None
    to_room_id: uuid.UUID | None = None
    reason: str | None = None
    moved_by_id: uuid.UUID
    moved_at: datetime
    document_id: uuid.UUID | None = None


# --- Списание ---
class WriteOffCreate(BaseModel):
    asset_id: uuid.UUID
    reason: str = Field(min_length=1)
    commission_members: str | None = None
    write_off_date: date | None = None


class WriteOffUpdate(BaseModel):
    reason: str | None = None
    commission_members: str | None = None
    write_off_date: date | None = None


class WriteOffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    reason: str
    commission_members: str | None = None
    write_off_date: date | None = None
    document_id: uuid.UUID | None = None
    created_by_id: uuid.UUID
    status: str
    created_at: datetime


class StatusChangeRequest(BaseModel):
    """Запрос на смену статуса документа (согласование/утверждение)."""
    status: str = Field(min_length=1, max_length=32)
    comment: str | None = None


# --- Ремонт ---
class RepairCreate(BaseModel):
    asset_id: uuid.UUID
    contractor: str | None = Field(default=None, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    cost: Decimal | None = None
    warranty_until: date | None = None
    is_guarantee: bool = False
    act_number: str | None = Field(default=None, max_length=64)


class RepairUpdate(BaseModel):
    contractor: str | None = Field(default=None, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    cost: Decimal | None = None
    warranty_until: date | None = None
    is_guarantee: bool | None = None
    act_number: str | None = Field(default=None, max_length=64)


class RepairOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    contractor: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    cost: Decimal | None = None
    warranty_until: date | None = None
    is_guarantee: bool
    act_number: str | None = None
    document_id: uuid.UUID | None = None
    created_by_id: uuid.UUID
    created_at: datetime


# --- Выдача / возврат ---
class IssuanceCreate(BaseModel):
    asset_id: uuid.UUID
    issued_to_id: uuid.UUID
    expected_return: datetime | None = None
    reason: str | None = None


class IssuanceReturnRequest(BaseModel):
    returned_condition: str | None = None


class IssuanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    issued_to_id: uuid.UUID
    issued_by_id: uuid.UUID
    issued_at: datetime | None = None
    return_at: datetime | None = None
    expected_return: datetime | None = None
    reason: str | None = None
    returned_condition: str | None = None
    is_returned: bool
    created_by_id: uuid.UUID