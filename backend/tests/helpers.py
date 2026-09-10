"""Вспомогательные функции для интеграционных тестов."""

from __future__ import annotations

import uuid


async def create_building(client, headers: dict, name: str = "Корпус 1"):
    resp = await client.post(
        "/structure/buildings",
        json={"name": name, "address": "ул. Школьная, 1"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def create_room(client, headers: dict, building_id: str, name: str = "Каб. 101"):
    resp = await client.post(
        "/structure/rooms",
        json={"building_id": building_id, "name": name, "room_number": "101"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def create_asset_type(client, headers: dict, code: str, name: str = "Оборудование"):
    resp = await client.post(
        "/reference/asset-types",
        json={"code": code, "name": name},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def create_asset(
    client,
    headers: dict,
    asset_type_id: str,
    room_id: str | None = None,
    name: str = "Проектор",
):
    inventory_number = f"TEST-{uuid.uuid4().hex[:8]}"
    payload = {
        "asset_type_id": asset_type_id,
        "room_id": room_id,
        "name": name,
        "serial_number": f"SER-{uuid.uuid4().hex[:6]}",
        "purchase_year": 2024,
        "cost": "15000.00",
        "quantity": "1",
        "use_custom_number": True,
        "inventory_number": inventory_number,
    }
    resp = await client.post("/assets", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()