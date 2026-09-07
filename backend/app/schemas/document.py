"""Pydantic-схемы для документов."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    doc_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    asset_id: uuid.UUID | None = None
    inventory_id: uuid.UUID | None = None
    write_off_id: uuid.UUID | None = None
    repair_id: uuid.UUID | None = None


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doc_number: str
    doc_type: str
    title: str
    description: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    status: str
    signer_user_id: uuid.UUID | None = None
    signed_at: datetime | None = None
    signer_role: str | None = None
    created_by_id: uuid.UUID
    asset_id: uuid.UUID | None = None
    inventory_id: uuid.UUID | None = None
    write_off_id: uuid.UUID | None = None
    repair_id: uuid.UUID | None = None
    created_at: datetime


class DocumentSignRequest(BaseModel):
    comment: str | None = None