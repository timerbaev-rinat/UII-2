"""Сервис аудита: запись действий в audit_log.

Используется всеми модулями для журналирования изменений.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    ip_address: str | None = None,
    comment: str | None = None,
) -> None:
    """Создаёт запись в журнале действий."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        comment=comment,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    # Коммит не делаем — вызывающий код управляет транзакцией.
    await db.flush()