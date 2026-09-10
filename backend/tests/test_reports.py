"""Тесты генерации отчётов (Excel/CSV/JSON/PDF)."""

import json

from tests.conftest import login
from tests.helpers import create_asset, create_asset_type, create_building, create_room


async def _seed_one_asset(client, headers):
    building = await create_building(client, headers)
    room = await create_room(client, headers, building["id"])
    asset_type = await create_asset_type(client, headers, code="EQP")
    return await create_asset(client, headers, asset_type["id"], room["id"], "Проектор")


async def _create_report(client, headers, fmt: str):
    resp = await client.post(
        "/reports",
        json={"report_type": "inventory_list", "format": fmt},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    job = resp.json()
    assert job["status"] == "COMPLETED", job
    return job


async def test_report_json(client):
    headers = await login(client, "zavhoz")
    asset = await _seed_one_asset(client, headers)
    job = await _create_report(client, headers, "JSON")

    resp = await client.get(f"/reports/{job['id']}/download", headers=headers)
    assert resp.status_code == 200
    rows = json.loads(resp.content.decode("utf-8"))
    assert any(r.get("Инвентарный номер") == asset["inventory_number"] for r in rows)


async def test_report_csv(client):
    headers = await login(client, "zavhoz")
    await _seed_one_asset(client, headers)
    job = await _create_report(client, headers, "CSV")
    resp = await client.get(f"/reports/{job['id']}/download", headers=headers)
    assert resp.status_code == 200
    assert b"\xef\xbb\xbf" in resp.content  # BOM для Excel


async def test_report_excel(client):
    headers = await login(client, "zavhoz")
    await _seed_one_asset(client, headers)
    job = await _create_report(client, headers, "EXCEL")
    resp = await client.get(f"/reports/{job['id']}/download", headers=headers)
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"  # zip-сигнатура xlsx


async def test_report_pdf(client):
    headers = await login(client, "zavhoz")
    await _seed_one_asset(client, headers)
    job = await _create_report(client, headers, "PDF")
    resp = await client.get(f"/reports/{job['id']}/download", headers=headers)
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"