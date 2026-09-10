"""Эндпоинты карточек имущества и постановки на учёт (Этап 4).

- CRUD карточек имущества
- Автоматическая нумерация + резервирование номеров
- Поиск и фильтрация по типу/комнате/статусу/ответственному
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DbSession, Perm, require_permission
from app.models import Asset, AssetNumberReservation, AssetType
from app.schemas.asset import (
    AssetCreate,
    AssetListOut,
    AssetOut,
    AssetUpdate,
    ReserveNumberOut,
    ReserveNumberRequest,
)
from app.services.audit import write_audit
from app.services.numbering import generate_number
from app.services.storage import IMAGE_EXTENSIONS, delete_file, media_type_for, resolve_path, save_upload

router = APIRouter()


def _get_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


async def _get_asset_or_404(db: AsyncSession, asset_id: uuid.UUID) -> Asset:
    asset = await db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Карточка имущества не найдена")
    return asset


@router.get(
    "",
    response_model=list[AssetListOut],
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Список карточек имущества",
)
async def list_assets(
    db: DbSession,
    query: str | None = None,
    asset_type_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    responsible_user_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Asset).order_by(Asset.created_at.desc())
    if query:
        like = f"%{query}%"
        stmt = stmt.where(
            or_(
                Asset.name.ilike(like),
                Asset.inventory_number.ilike(like),
                Asset.serial_number.ilike(like),
            )
        )
    if asset_type_id:
        stmt = stmt.where(Asset.asset_type_id == asset_type_id)
    if room_id:
        stmt = stmt.where(Asset.room_id == room_id)
    if status_filter:
        stmt = stmt.where(Asset.status == status_filter)
    if responsible_user_id:
        stmt = stmt.where(Asset.responsible_user_id == responsible_user_id)
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "",
    response_model=AssetOut,
    dependencies=[Depends(require_permission(Perm.CREATE_CARD))],
    summary="Постановка имущества на учёт",
)
async def create_asset(
    payload: AssetCreate,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    asset_type = await db.get(AssetType, payload.asset_type_id)
    if asset_type is None:
        raise HTTPException(status_code=400, detail="Тип объекта не найден")

    inventory_number = payload.inventory_number
    if payload.use_custom_number:
        if not inventory_number:
            raise HTTPException(
                status_code=400, detail="Укажите inventory_number при use_custom_number=True"
            )
        exists = await db.execute(
            select(Asset).where(Asset.inventory_number == inventory_number)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Инвентарный номер уже занят")
    else:
        inventory_number = await generate_number(
            db, asset_type=asset_type, reserved_by_id=user.id
        )

    asset = Asset(
        inventory_number=inventory_number,
        asset_type_id=payload.asset_type_id,
        room_id=payload.room_id,
        name=payload.name,
        model=payload.model,
        brand=payload.brand,
        serial_number=payload.serial_number,
        purchase_year=payload.purchase_year,
        commissioning_date=payload.commissioning_date,
        warranty_until=payload.warranty_until,
        quantity=payload.quantity,
        unit=payload.unit,
        material=payload.material,
        cost=payload.cost,
        description=payload.description,
        photo_path=payload.photo_path,
        custom_attributes=payload.custom_attributes,
        responsible_user_id=payload.responsible_user_id,
    )
    db.add(asset)
    await db.flush()

    # Привязываем резервацию к созданной карточке (если генерировали номер)
    if not payload.use_custom_number:
        res = await db.execute(
            select(AssetNumberReservation).where(
                AssetNumberReservation.inventory_number == inventory_number,
                AssetNumberReservation.is_used.is_(False),
            )
        )
        reservation = res.scalar_one_or_none()
        if reservation:
            reservation.is_used = True
            reservation.asset_id = asset.id

    await write_audit(
        db,
        user_id=user.id,
        action="CREATE",
        entity_type="asset",
        entity_id=str(asset.id),
        new_value=inventory_number,
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get(
    "/{asset_id}",
    response_model=AssetOut,
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Карточка имущества",
)
async def get_asset(asset_id: uuid.UUID, db: DbSession):
    return await _get_asset_or_404(db, asset_id)


@router.post(
    "/{asset_id}/photo",
    response_model=AssetOut,
    dependencies=[Depends(require_permission(Perm.EDIT_CARD))],
    summary="Загрузка фото карточки",
)
async def upload_asset_photo(
    asset_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    request: Request,
    file: UploadFile = File(...),
):
    asset = await _get_asset_or_404(db, asset_id)
    rel_path, _, _ = await save_upload(
        file, subdir=f"assets/{asset.inventory_number}", allowed_extensions=IMAGE_EXTENSIONS
    )
    # Удаляем старое фото, если было
    if asset.photo_path:
        delete_file(asset.photo_path)
    asset.photo_path = rel_path

    await write_audit(
        db,
        user_id=user.id,
        action="UPLOAD_PHOTO",
        entity_type="asset",
        entity_id=str(asset.id),
        new_value=rel_path,
        ip_address=_get_client_ip(request) if request else None,
    )
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get(
    "/{asset_id}/photo",
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Фото карточки",
)
async def get_asset_photo(asset_id: uuid.UUID, db: DbSession):
    asset = await _get_asset_or_404(db, asset_id)
    if not asset.photo_path:
        raise HTTPException(status_code=404, detail="Фото не загружено")
    path = resolve_path(asset.photo_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл фото не найден")
    return FileResponse(path, media_type=media_type_for(asset.photo_path))


@router.patch(
    "/{asset_id}",
    response_model=AssetOut,
    dependencies=[Depends(require_permission(Perm.EDIT_CARD))],
    summary="Обновление карточки",
)
async def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    asset = await _get_asset_or_404(db, asset_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(asset, field, value)

    await write_audit(
        db,
        user_id=user.id,
        action="UPDATE",
        entity_type="asset",
        entity_id=str(asset.id),
        comment=f"Обновлены поля: {', '.join(data.keys())}",
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete(
    "/{asset_id}",
    dependencies=[Depends(require_permission(Perm.DELETE_CARD))],
    summary="Удаление карточки",
)
async def delete_asset(
    asset_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    asset = await _get_asset_or_404(db, asset_id)
    await write_audit(
        db,
        user_id=user.id,
        action="DELETE",
        entity_type="asset",
        entity_id=str(asset.id),
        new_value=asset.inventory_number,
        ip_address=_get_client_ip(request),
    )
    await db.delete(asset)
    await db.commit()
    return {"detail": "Карточка удалена"}


@router.post(
    "/reserve",
    response_model=ReserveNumberOut,
    dependencies=[Depends(require_permission(Perm.CREATE_CARD))],
    summary="Резервирование инвентарного номера",
)
async def reserve_number(
    payload: ReserveNumberRequest,
    db: DbSession,
    user: CurrentUser,
):
    asset_type = await db.get(AssetType, payload.asset_type_id)
    if asset_type is None:
        raise HTTPException(status_code=400, detail="Тип объекта не найден")

    number = await generate_number(db, asset_type=asset_type, reserved_by_id=user.id)
    await db.commit()

    return ReserveNumberOut(inventory_number=number)


@router.get(
    "/stats/summary",
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Сводная статистика по карточкам",
)
async def asset_stats(db: DbSession):
    total = await db.scalar(select(func.count()).select_from(Asset))
    by_status = {}
    result = await db.execute(
        select(Asset.status, func.count()).group_by(Asset.status)
    )
    for row in result.all():
        by_status[row[0]] = row[1]
    return {"total": int(total or 0), "by_status": by_status}