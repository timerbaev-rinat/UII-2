"""Утилиты безопасности: хэширование паролей, генерация и проверка JWT.

- Хэширование паролей через passlib (bcrypt).
- JWT access/refresh токены через PyJWT.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt — алгоритм хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Отдельный контекст для refresh-токенов (тип токена в payload)
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    """Возвращает хэш пароля."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль по хэшу."""
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    *,
    user_id: uuid.UUID,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    """Создаёт JWT-токен."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: uuid.UUID, extra: dict[str, Any] | None = None) -> str:
    """Создаёт access-токен."""
    return _create_token(
        user_id=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra=extra,
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Создаёт refresh-токен (долгий срок жизни)."""
    return _create_token(
        user_id=user_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует JWT. Возбуждает исключение при невалидности."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])