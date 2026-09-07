"""Pydantic-схемы для аудита."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    ip_address: str | None = None
    comment: str | None = None
    created_at: datetime