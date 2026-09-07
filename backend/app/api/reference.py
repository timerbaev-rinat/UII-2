"""Эндпоинты справочников: типы объектов, атрибуты, состояния, единицы, материалы (Этап 3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession, Perm, require_permission
from app.models import AssetAttribute, AssetType, AssetStatus, Material, UnitOfMeasure
from app.schemas.structure import (
    AssetAttributeCreate,
    AssetAttributeOut,
    AssetTypeCreate,
    AssetTypeOut,
    AssetStatusCreate,
    AssetStatusOut,
    MaterialCreate,
    MaterialOut,
    UnitCreate,
    UnitOut,
)

router = APIRouter()

VIEW = Depends(require_permission(Perm.VIEW_CARDS))
MANAGE = Depends(require_permission(Perm.MANAGE_REFERENCES))


# --- Типы объектов ---
@router.get("/asset-types", response_model=list[AssetTypeOut], dependencies=[VIEW])
async def list_asset_types(db: DbSession):
    result = await db.execute(select(AssetType).order_by(AssetType.name))
    return result.scalars().all()


@router.post("/asset-types", response_model=AssetTypeOut, dependencies=[MANAGE])
async def create_asset_type(payload: AssetTypeCreate, db: DbSession):
    asset_type = AssetType(**payload.model_dump())
    db.add(asset_type)
    await db.commit()
    await db.refresh(asset_type)
    return asset_type


@router.patch("/asset-types/{type_id}", response_model=AssetTypeOut, dependencies=[MANAGE])
async def update_asset_type(type_id: uuid.UUID, payload: AssetTypeCreate, db: DbSession):
    asset_type = await db.get(AssetType, type_id)
    if asset_type is None:
        raise HTTPException(status_code=404, detail="Тип не найден")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(asset_type, k, v)
    await db.commit()
    await db.refresh(asset_type)
    return asset_type


# --- Атрибуты типа (шаблон карточки) ---
@router.get(
    "/asset-types/{type_id}/attributes",
    response_model=list[AssetAttributeOut],
    dependencies=[VIEW],
)
async def list_attributes(type_id: uuid.UUID, db: DbSession):
    result = await db.execute(
        select(AssetAttribute)
        .where(AssetAttribute.asset_type_id == type_id)
        .order_by(AssetAttribute.sort_order)
    )
    return result.scalars().all()


@router.post(
    "/asset-types/{type_id}/attributes",
    response_model=AssetAttributeOut,
    dependencies=[MANAGE],
)
async def create_attribute(type_id: uuid.UUID, payload: AssetAttributeCreate, db: DbSession):
    if await db.get(AssetType, type_id) is None:
        raise HTTPException(status_code=404, detail="Тип не найден")
    attr = AssetAttribute(asset_type_id=type_id, **payload.model_dump())
    db.add(attr)
    await db.commit()
    await db.refresh(attr)
    return attr


@router.delete(
    "/asset-types/attributes/{attr_id}",
    dependencies=[MANAGE],
)
async def delete_attribute(attr_id: uuid.UUID, db: DbSession):
    attr = await db.get(AssetAttribute, attr_id)
    if attr is None:
        raise HTTPException(status_code=404, detail="Атрибут не найден")
    await db.delete(attr)
    await db.commit()
    return {"detail": "Атрибут удалён"}


# --- Состояния ---
@router.get("/statuses", response_model=list[AssetStatusOut], dependencies=[VIEW])
async def list_statuses(db: DbSession):
    result = await db.execute(select(AssetStatus).order_by(AssetStatus.name))
    return result.scalars().all()


@router.post("/statuses", response_model=AssetStatusOut, dependencies=[MANAGE])
async def create_status(payload: AssetStatusCreate, db: DbSession):
    status = AssetStatus(**payload.model_dump(), is_active=True)
    db.add(status)
    await db.commit()
    await db.refresh(status)
    return status


# --- Единицы измерения ---
@router.get("/units", response_model=list[UnitOut], dependencies=[VIEW])
async def list_units(db: DbSession):
    result = await db.execute(select(UnitOfMeasure).order_by(UnitOfMeasure.name))
    return result.scalars().all()


@router.post("/units", response_model=UnitOut, dependencies=[MANAGE])
async def create_unit(payload: UnitCreate, db: DbSession):
    unit = UnitOfMeasure(**payload.model_dump(), is_active=True)
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit


# --- Материалы ---
@router.get("/materials", response_model=list[MaterialOut], dependencies=[VIEW])
async def list_materials(db: DbSession):
    result = await db.execute(select(Material).order_by(Material.name))
    return result.scalars().all()


@router.post("/materials", response_model=MaterialOut, dependencies=[MANAGE])
async def create_material(payload: MaterialCreate, db: DbSession):
    material = Material(**payload.model_dump(), is_active=True)
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material