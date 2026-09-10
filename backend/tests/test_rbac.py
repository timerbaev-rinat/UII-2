"""Интеграционные тесты разграничения прав (RBAC)."""

import uuid

from tests.conftest import login


async def test_municipality_can_view_assets(client):
    headers = await login(client, "muni")
    resp = await client.get("/assets", headers=headers)
    assert resp.status_code == 200


async def test_municipality_cannot_create_asset(client):
    headers = await login(client, "muni")
    payload = {
        "asset_type_id": str(uuid.uuid4()),
        "name": "X",
        "use_custom_number": True,
        "inventory_number": "NOPE-1",
    }
    resp = await client.post("/assets", json=payload, headers=headers)
    # До проверки существования типа срабатывает проверка прав => 403
    assert resp.status_code == 403


async def test_municipality_cannot_manage_users(client):
    headers = await login(client, "muni")
    resp = await client.get("/auth/users", headers=headers)
    assert resp.status_code == 403


async def test_municipality_cannot_approve_writeoff(client):
    headers = await login(client, "muni")
    resp = await client.post(
        f"/operations/write-offs/{uuid.uuid4()}/status",
        json={"status": "APPROVED"},
        headers=headers,
    )
    # Проверка разрешения выполняется до поиска акта => 403
    assert resp.status_code == 403


async def test_zavhoz_can_manage_structure(client):
    headers = await login(client, "zavhoz")
    resp = await client.post(
        "/structure/buildings", json={"name": "Корпус B"}, headers=headers
    )
    assert resp.status_code == 200


async def test_director_can_view_reports(client):
    headers = await login(client, "director")
    resp = await client.get("/reports", headers=headers)
    assert resp.status_code == 200


async def test_admin_can_manage_users(client):
    headers = await login(client, "admin")
    resp = await client.get("/auth/users", headers=headers)
    assert resp.status_code == 200