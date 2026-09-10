"""Сервис хранения загружаемых файлов (фото, документы).

Обеспечивает:
- валидацию расширений и MIME-типов;
- ограничение максимального размера;
- сохранение под уникальным именем внутри `settings.upload_dir`;
- безопасное разрешение пути (защита от path traversal);
- удаление файла по сохранённому относительному пути.

Хранение локально на диске (см. `settings.upload_dir`). В дальнейшем
может быть заменено на объектное хранилище.
"""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import Set

from fastapi import HTTPException, UploadFile, status

from app.config import settings

# Допустимые расширения
IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DOCUMENT_EXTENSIONS: Set[str] = IMAGE_EXTENSIONS | {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".rtf",
    ".odt",
    ".ods",
}

# Допустимые MIME-типы (проверка заголовка запроса)
ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
    "application/rtf",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
}


def _max_size_bytes() -> int:
    return settings.max_upload_size_mb * 1024 * 1024


# Сигнатуры (magic bytes) для проверки фактического формата изображений.
_IMAGE_MAGIC = {
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".webp": (b"RIFF",),  # + "WEBP" на смещении 8
}


def _check_image_magic(content: bytes, ext: str) -> None:
    """Проверяет сигнатуру файла против расширения (защита от подделки)."""
    signatures = _IMAGE_MAGIC.get(ext)
    if not signatures:
        return
    if any(content.startswith(sig) for sig in signatures):
        if ext == ".webp":
            # RIFF ... + "WEBP" на байтах 8..11
            if len(content) >= 12 and content[8:12] == b"WEBP":
                return
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл не является корректным изображением WebP",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Содержимое файла не соответствует расширению «{ext}»",
    )


async def save_upload(
    file: UploadFile,
    *,
    subdir: str,
    allowed_extensions: Set[str],
) -> tuple[str, str, int]:
    """Сохраняет загруженный файл, возвращает (относительный путь, имя файла, размер).

    - Проверяет расширение по whitelist.
    - Проверяет непустоту и максимальный размер.
    - Сохраняет под уникальным UUID-именем в `<upload_dir>/<subdir>/`.
    """
    original_name = file.filename or "file"
    ext = Path(original_name).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла «{ext}». Разрешены: "
            f"{', '.join(sorted(allowed_extensions))}",
        )

    # Дополнительная проверка MIME-типа, если он указан клиентом
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый MIME-тип «{file.content_type}»",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пуст"
        )
    if len(content) > _max_size_bytes():
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл превышает максимальный размер {settings.max_upload_size_mb} МБ",
        )

    # Проверка фактического формата изображений (защита от подделки расширения)
    if ext in IMAGE_EXTENSIONS:
        _check_image_magic(content, ext)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    rel_dir = Path(subdir)
    target_dir = Path(settings.upload_dir) / rel_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / unique_name
    target.write_bytes(content)

    rel_path = (rel_dir / unique_name).as_posix()
    return rel_path, original_name, len(content)


def resolve_path(rel_path: str) -> Path:
    """Возвращает абсолютный путь к файлу, защищая от выхода за пределы upload_dir."""
    upload_root = Path(settings.upload_dir).resolve()
    candidate = (upload_root / rel_path).resolve()
    if not candidate.is_relative_to(upload_root):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный путь к файлу"
        )
    return candidate


def delete_file(rel_path: str | None) -> None:
    """Удаляет файл по относительному пути, если он существует."""
    if not rel_path:
        return
    try:
        path = resolve_path(rel_path)
        if path.is_file():
            path.unlink()
    except HTTPException:
        # Путь вне корня — не удаляем
        return


def media_type_for(path: str) -> str:
    """Определяет media_type по расширению файла."""
    return mimetypes.guess_type(path)[0] or "application/octet-stream"