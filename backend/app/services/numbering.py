"""Сервис генерации инвентарных номеров и резервирования.

Шаблон: {Год}-{Тип}-{№} — настраивается в asset_types.number_template.
Поддерживаются плейсхолдеры:
  {Год}   — текущий год
  {Тип}   — код типа объекта (asset_type.code)
  {№}     — порядковый номер (автоинкремент)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, AssetNumberReservation, AssetType

# Плейсхолдеры шаблона
DEFAULT_TEMPLATE = "{Год}-{Тип}-{№}"


def _safe_filename_template(template: str) -> str:
    return template or DEFAULT_TEMPLATE


async def _next_sequence(db: AsyncSession, asset_type_code: str) -> int:
    """Возвращает следующий порядковый номер для типа в текущем году."""
    year = datetime.now().year
    prefix = f"{year}-{asset_type_code}-"
    count = await db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(Asset.inventory_number.like(f"{prefix}%"))
    )
    used_res = await db.scalar(
        select(func.count())
        .select_from(AssetNumberReservation)
        .where(AssetNumberReservation.inventory_number.like(f"{prefix}%"))
    )
    return int(count or 0) + int(used_res or 0) + 1


def _render(template: str, year: int, type_code: str, seq: int) -> str:
    """Подставляет значения в шаблон."""
    return (
        template
        .replace("{Год}", str(year))
        .replace("{Тип}", type_code)
        .replace("{№}", str(seq))
    )


async def generate_number(
    db: AsyncSession,
    *,
    asset_type: AssetType,
    reserved_by_id,
) -> str:
    """Генерирует инвентарный номер и сразу резервирует его."""
    template = _safe_filename_template(asset_type.number_template)
    year = datetime.now().year
    seq = await _next_sequence(db, asset_type.code)
    number = _render(template, year, asset_type.code, seq)

    # Создаём резервацию
    reservation = AssetNumberReservation(
        inventory_number=number,
        asset_type_id=asset_type.id,
        reserved_by_id=reserved_by_id,
        is_used=False,
    )
    db.add(reservation)
    await db.flush()
    return number