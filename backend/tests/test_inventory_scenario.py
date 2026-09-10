"""Интеграционный сценарий: поступление → учёт → перемещение → инвентаризация → списание."""

from tests.conftest import login
from tests.helpers import (
    create_asset,
    create_asset_type,
    create_building,
    create_room,
)


async def test_full_lifecycle_scenario(client):
    headers = await login(client, "zavhoz")

    # 1. Структура
    building = await create_building(client, headers)
    room1 = await create_room(client, headers, building["id"], "Каб. 101")
    room2 = await create_room(client, headers, building["id"], "Каб. 102")

    # 2. Справочник типа
    asset_type = await create_asset_type(client, headers, code="EQP")

    # 3. Постановка на учёт (поступление → карточка)
    asset = await create_asset(client, headers, asset_type["id"], room1["id"], "Проектор")
    assert asset["inventory_number"].startswith("TEST-")
    assert asset["room_id"] == room1["id"]

    # 4. Перемещение
    resp = await client.post(
        "/operations/moves",
        json={"asset_id": asset["id"], "to_room_id": room2["id"], "reason": "перенос"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    moved = resp.json()
    assert moved["to_room_id"] == room2["id"]

    asset = (await client.get(f"/assets/{asset['id']}", headers=headers)).json()
    assert asset["status"] == "MOVED"
    assert asset["room_id"] == room2["id"]

    # 5. Инвентаризация
    inv = (await client.post(
        "/inventories",
        json={"name": "Годовая", "inv_type": "PLANNED", "coverage": "FULL"},
        headers=headers,
    )).json()

    started = (await client.post(f"/inventories/{inv['id']}/start", headers=headers)).json()
    assert started["status"] == "IN_PROGRESS"

    items = (await client.get(f"/inventories/{inv['id']}/items", headers=headers)).json()
    assert len(items) >= 1
    item = items[0]
    assert item["asset_id"] == asset["id"]

    # Отметка факта (мобильный сценарий)
    upd = await client.patch(
        f"/inventories/{inv['id']}/items/{item['id']}",
        json={"is_checked": True, "actual_quantity": "1"},
        headers=headers,
    )
    assert upd.status_code == 200, upd.text

    completed = (await client.post(f"/inventories/{inv['id']}/complete", headers=headers)).json()
    assert completed["status"] == "COMPLETED"

    approved = (await client.post(
        f"/inventories/{inv['id']}/approve", json={"comment": "ок"}, headers=headers
    )).json()
    assert approved["status"] == "APPROVED"

    # 6. Списание и утверждение
    wo = (await client.post(
        "/operations/write-offs",
        json={"asset_id": asset["id"], "reason": "износ", "commission_members": "комиссия"},
        headers=headers,
    )).json()
    assert wo["status"] == "DRAFT"

    resp = await client.post(
        f"/operations/write-offs/{wo['id']}/status",
        json={"status": "APPROVED"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    asset = (await client.get(f"/assets/{asset['id']}", headers=headers)).json()
    assert asset["status"] == "WRITTEN_OFF"
    assert asset["write_off_date"] is not None