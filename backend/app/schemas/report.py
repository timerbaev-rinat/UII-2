"""Pydantic-схемы для отчётов."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    report_type: str = Field(min_length=1, max_length=64)
    format: str = Field(default="EXCEL", max_length=16)
    params: dict | None = None
    schedule_cron: str | None = Field(default=None, max_length=128)


class ReportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_type: str
    format: str
    status: str
    params: dict | None = None
    result_path: str | None = None
    error_message: str | None = None
    created_by_id: uuid.UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notified: bool
    schedule_cron: str | None = None
    created_at: datetime