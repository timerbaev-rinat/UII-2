"""Тесты сервиса хранения: валидация magic-bytes и защита путей."""

import pytest
from fastapi import HTTPException

from app.services.storage import _check_image_magic, resolve_path


def test_png_magic_accepted():
    # PNG signature + минимальный кусок
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
    _check_image_magic(content, ".png")  # не должно бросить


def test_jpeg_magic_accepted():
    _check_image_magic(b"\xff\xd8\xff\xe0" + b"\x00" * 4, ".jpg")


def test_webp_magic_checked():
    content = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 4
    _check_image_magic(content, ".webp")


def test_mismatched_extension_rejected():
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
    with pytest.raises(HTTPException):
        _check_image_magic(content, ".jpg")


def test_fake_webp_rejected():
    content = b"RIFF" + b"\x00" * 4 + b"XXXX" + b"\x00" * 4
    with pytest.raises(HTTPException):
        _check_image_magic(content, ".webp")


def test_resolve_path_blocks_traversal(monkeypatch, tmp_path):
    from app.services.storage import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    with pytest.raises(HTTPException):
        resolve_path("../../etc/passwd")