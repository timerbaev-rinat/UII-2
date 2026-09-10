"""Интеграционные тесты аутентификации."""

from tests.conftest import login


async def test_login_success_returns_tokens(client):
    resp = await client.post(
        "/auth/login", json={"login": "admin", "password": "pass123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]


async def test_login_wrong_password(client):
    resp = await client.post("/auth/login", json={"login": "admin", "password": "bad"})
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post("/auth/login", json={"login": "ghost", "password": "pass123"})
    assert resp.status_code == 401


async def test_me_with_valid_token(client):
    headers = await login(client, "admin")
    resp = await client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["login"] == "admin"


async def test_me_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_refresh_flow(client):
    login_resp = await client.post(
        "/auth/login", json={"login": "admin", "password": "pass123"}
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_change_password_roundtrip(client):
    headers = await login(client, "admin")
    resp = await client.post(
        "/auth/change-password",
        json={"old_password": "pass123", "new_password": "newpass456"},
        headers=headers,
    )
    assert resp.status_code == 200
    # Старый пароль больше не подходит
    resp = await client.post("/auth/login", json={"login": "admin", "password": "pass123"})
    assert resp.status_code == 401
    resp = await client.post("/auth/login", json={"login": "admin", "password": "newpass456"})
    assert resp.status_code == 200