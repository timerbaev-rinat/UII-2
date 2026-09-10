"""Тестовая инфраструктура.

Для запуска тестов требуется работающий PostgreSQL (например, из
docker-compose). База тестов задаётся через TEST_DATABASE_URL (по умолчанию
`asset_school_test`). Схема создаётся автоматически при импорте conftest,
данные между тестами изолируются (TRUNCATE + повторный сидинг ролей).

Запуск:
    cd backend
    pip install -r requirements-dev.txt
    pytest
"""

from __future__ import annotations

import asyncio
import os
import re
import uuid

# --- Важно: настройки должны быть установлены ДО импорта приложения ---
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://asset_user:change_me_strong_password@localhost:5432/"
    "asset_school_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["SECURITY_HEADERS"] = "false"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Permission,
    Role,
    User,
)
from app.core.security import hash_password  # noqa: E402
from app.seed import (  # noqa: E402
    ROLE_ADMIN,
    ROLE_DIRECTOR,
    ROLE_MUNICIPALITY,
    ROLE_NAMES,
    ROLE_PERMISSIONS,
    ROLE_ZAVHOZ,
)

ALL_PERMISSION_CODES = list(ROLE_PERMISSIONS[ROLE_ADMIN])


def _parse_db_url(url: str) -> tuple[str, str, str, int, str]:
    m = re.match(r"postgresql(?:\+asyncpg)?://([^:]+):([^@]+)@([^:]+):(\d+)/(\w+)", url)
    if not m:
        raise RuntimeError(f"Не удалось разобрать TEST_DATABASE_URL: {url}")
    return m.group(1), m.group(2), m.group(3), int(m.group(4)), m.group(5)


async def _ensure_database() -> None:
    """Создаёт тестовую БД, если её нет."""
    user, password, host, port, dbname = _parse_db_url(TEST_DATABASE_URL)
    import asyncpg

    conn = await asyncpg.connect(
        user=user, password=password, host=host, port=port, database="postgres"
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", dbname)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        await conn.close()


async def _create_schema() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


# Создание БД и схемы выполняется один раз при импорте conftest.
asyncio.run(_ensure_database())
asyncio.run(_create_schema())


async def _truncate_all(engine) -> None:  # noqa: ANN001
    """Очищает все таблицы (с учётом FK) без сброса схемы."""
    async with engine.begin() as conn:
        await conn.execute(text("SET session_replication_role = replica"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        await conn.execute(text("SET session_replication_role = DEFAULT"))


async def _seed_base(session) -> dict[str, Role]:  # noqa: ANN001
    """Создаёт разрешения, роли и базовых пользователей."""
    perms: dict[str, Permission] = {}
    for code in ALL_PERMISSION_CODES:
        perm = Permission(code=code, name=code, description=code)
        session.add(perm)
        perms[code] = perm
    await session.flush()

    roles: dict[str, Role] = {}
    for code, name in ROLE_NAMES.items():
        role = Role(code=code, name=name, description=f"Роль «{name}»")
        role.permissions = [perms[p] for p in ROLE_PERMISSIONS[code]]
        session.add(role)
        roles[code] = role
    await session.flush()

    # Администратор + тестовые пользователи по ролям
    test_users = [
        ("admin", ROLE_ADMIN),
        ("zavhoz", ROLE_ZAVHOZ),
        ("director", ROLE_DIRECTOR),
        ("muni", ROLE_MUNICIPALITY),
    ]
    for login, role_code in test_users:
        user = User(
            login=login,
            full_name=f"Тест {login}",
            position="Тест",
            password_hash=hash_password("pass123"),
            is_active=True,
            roles=[roles[role_code]],
        )
        session.add(user)
    await session.flush()
    return roles


@pytest_asyncio.fixture
async def prepared_app():
    """Подготавливает приложение для теста: чистая БД, сидинг, override get_db."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    await _truncate_all(engine)
    async with factory() as session:
        await _seed_base(session)
        await session.commit()

    async def _override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


@pytest_asyncio.fixture
async def client(prepared_app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def login(client: AsyncClient, login_: str, password: str = "pass123"):
    resp = await client.post(
        "/auth/login",
        json={"login": login_, "password": password},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def admin_headers(client):
    return await login(client, "admin")


@pytest_asyncio.fixture
async def zavhoz_headers(client):
    return await login(client, "zavhoz")


@pytest_asyncio.fixture
async def muni_headers(client):
    return await login(client, "muni")


def new_uuid() -> str:
    return str(uuid.uuid4())