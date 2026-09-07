"""Модели отчётов: очередь задач генерации, расписание."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUID_PK, TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class ReportStatusEnum(str, enum.Enum):
    """Статусы задачи генерации отчёта."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReportFormatEnum(str, enum.Enum):
    """Форматы отчётов."""

    EXCEL = "EXCEL"
    PDF = "PDF"
    CSV = "CSV"
    JSON = "JSON"
    XML = "XML"


class ReportJob(TimestampMixin, Base):
    """Очередь задач генерации отчётов."""

    __tablename__ = "report_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    # тип отчёта: inventory_list, asset_statement, depreciation, discrepancies, write_off_act
    report_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    format: Mapped[ReportFormatEnum] = mapped_column(
        String(16), default=ReportFormatEnum.EXCEL.value, nullable=False
    )
    status: Mapped[ReportStatusEnum] = mapped_column(
        String(16), default=ReportStatusEnum.PENDING.value, nullable=False, index=True
    )
    # параметры отчёта (JSON)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK, ForeignKey("users.id"), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # уведомление о готовности
    notified: Mapped[bool] = mapped_column(default=False, nullable=False)
    # расписание (cron-строка), если отчёт автоматический
    schedule_cron: Mapped[str | None] = mapped_column(String(128), nullable=True)