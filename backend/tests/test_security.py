"""Юнит-тесты безопасности: хэширование паролей и JWT."""

import uuid

from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("Secret123")
    assert h != "Secret123"
    assert verify_password("Secret123", h)


def test_password_wrong_fails():
    h = hash_password("Secret123")
    assert not verify_password("wrong", h)


def test_access_token_type_and_subject():
    uid = uuid.uuid4()
    token = create_access_token(uid)
    payload = decode_token(token)
    assert payload["type"] == ACCESS_TOKEN_TYPE
    assert payload["sub"] == str(uid)


def test_refresh_token_type():
    token = create_refresh_token(uuid.uuid4())
    assert decode_token(token)["type"] == REFRESH_TOKEN_TYPE


def test_decode_expired_or_invalid_raises():
    import jwt

    try:
        decode_token("not-a-token")
        raise AssertionError("ожидалось исключение")
    except jwt.PyJWTError:
        pass