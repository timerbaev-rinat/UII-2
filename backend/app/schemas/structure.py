"""Pydantic-схемы для структуры (здания, кабинеты) и справочников."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Здания ---
class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = None
    building_code: str | None = Field(default=None, max_length=32)
    description: str | None = None


class BuildingUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    building_code: str | None = Field(default=None, max_length=32)
    description: str | None = None


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: str | None = None
    building_code: str | None = None
    description: str | None = None
    created_at: datetime


# --- Кабинеты ---
class RoomCreate(BaseModel):
    building_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    room_number: str | None = Field(default=None, max_length=32)
    room_type: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=255)
    description: str | None = None


class RoomUpdate(BaseModel):
    building_id: uuid.UUID | None = None
    name: str | None = Field(default=None, max_length=255)
    room_number: str | None = Field(default=None, max_length=32)
    room_type: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=255)
    description: str | None = None


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    building_id: uuid.UUID
    name: str
    room_number: str | None = None
    room_type: str | None = None
    department: str | None = None
    description: str | None = None
    created_at: datetime


# --- Справочники ---
class AssetStatusCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class AssetStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_active: bool


class UnitCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    abbreviation: str | None = Field(default=None, max_length=16)


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    abbreviation: str | None = None
    is_active: bool


class MaterialCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_active: bool


class AssetTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    number_template: str | None = Field(default=None, max_length=255)


class AssetAttributeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    value_type: str = Field(default="string", max_length=32)
    is_required: bool = False
    sort_order: int = 0


class AssetTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    number_template: str | None = None


class AssetAttributeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_type_id: uuid.UUID
    name: str
    value_type: str
    is_required: bool
    sort_order: int