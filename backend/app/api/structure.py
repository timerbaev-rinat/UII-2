"""Эндпоинты структуры учреждения: здания и кабинеты/помещения (Этап 3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession, Perm, require_permission
from app.models import Building, Room
from app.schemas.structure import (
    BuildingCreate,
    BuildingOut,
    BuildingUpdate,
    RoomCreate,
    RoomOut,
    RoomUpdate,
)

router = APIRouter()

# Общие права
VIEW = Depends(require_permission(Perm.VIEW_CARDS))
MANAGE = Depends(require_permission(Perm.MANAGE_STRUCTURE))


@router.get("/buildings", response_model=list[BuildingOut], dependencies=[VIEW])
async def list_buildings(db: DbSession):
    result = await db.execute(select(Building).order_by(Building.name))
    return result.scalars().all()


@router.post("/buildings", response_model=BuildingOut, dependencies=[MANAGE])
async def create_building(payload: BuildingCreate, db: DbSession):
    building = Building(**payload.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    return building


@router.get("/buildings/{building_id}", response_model=BuildingOut, dependencies=[VIEW])
async def get_building(building_id: uuid.UUID, db: DbSession):
    building = await db.get(Building, building_id)
    if building is None:
        raise HTTPException(status_code=404, detail="Здание не найдено")
    return building


@router.patch("/buildings/{building_id}", response_model=BuildingOut, dependencies=[MANAGE])
async def update_building(building_id: uuid.UUID, payload: BuildingUpdate, db: DbSession):
    building = await db.get(Building, building_id)
    if building is None:
        raise HTTPException(status_code=404, detail="Здание не найдено")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(building, k, v)
    await db.commit()
    await db.refresh(building)
    return building


@router.delete("/buildings/{building_id}", dependencies=[MANAGE])
async def delete_building(building_id: uuid.UUID, db: DbSession):
    building = await db.get(Building, building_id)
    if building is None:
        raise HTTPException(status_code=404, detail="Здание не найдено")
    await db.delete(building)
    await db.commit()
    return {"detail": "Здание удалено"}


@router.get("/rooms", response_model=list[RoomOut], dependencies=[VIEW])
async def list_rooms(db: DbSession, building_id: uuid.UUID | None = None):
    q = select(Room)
    if building_id is not None:
        q = q.where(Room.building_id == building_id)
    result = await db.execute(q.order_by(Room.building_id, Room.name))
    return result.scalars().all()


@router.post("/rooms", response_model=RoomOut, dependencies=[MANAGE])
async def create_room(payload: RoomCreate, db: DbSession):
    building = await db.get(Building, payload.building_id)
    if building is None:
        raise HTTPException(status_code=400, detail="Здание не найдено")
    room = Room(**payload.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/rooms/{room_id}", response_model=RoomOut, dependencies=[VIEW])
async def get_room(room_id: uuid.UUID, db: DbSession):
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    return room


@router.patch("/rooms/{room_id}", response_model=RoomOut, dependencies=[MANAGE])
async def update_room(room_id: uuid.UUID, payload: RoomUpdate, db: DbSession):
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    data = payload.model_dump(exclude_unset=True)
    if "building_id" in data and data["building_id"] is not None:
        if await db.get(Building, data["building_id"]) is None:
            raise HTTPException(status_code=400, detail="Здание не найдено")
    for k, v in data.items():
        setattr(room, k, v)
    await db.commit()
    await db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", dependencies=[MANAGE])
async def delete_room(room_id: uuid.UUID, db: DbSession):
    room = await db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Кабинет не найден")
    await db.delete(room)
    await db.commit()
    return {"detail": "Кабинет удалён"}