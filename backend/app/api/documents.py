"""Эндпоинты документов (Этап 7).

- Создание/обновление/список документов
- Нумерация документов по шаблону
- Смена статуса (черновик → согласование → утверждено), подпись
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DbSession, Perm, require_permission
from app.models import Document
from app.models.base import DocumentStatusEnum
from app.schemas.document import (
    DocumentCreate,
    DocumentOut,
    DocumentSignRequest,
    DocumentUpdate,
)
from app.schemas.operation import StatusChangeRequest
from app.services.audit import write_audit
from app.services.storage import (
    DOCUMENT_EXTENSIONS,
    delete_file,
    media_type_for,
    resolve_path,
    save_upload,
)

router = APIRouter()


def _get_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


async def _get_doc_or_404(db: AsyncSession, doc_id: uuid.UUID) -> Document:
    doc = await db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return doc


async def _next_doc_number(db: AsyncSession, doc_type: str) -> str:
    """Генерирует номер документа: {Год}-{Тип}-{№}."""
    year = datetime.now().year
    count = await db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.doc_type == doc_type)
    )
    seq = int(count or 0) + 1
    return f"{year}-{doc_type}-{seq}"


@router.get(
    "",
    response_model=list[DocumentOut],
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Список документов",
)
async def list_documents(db: DbSession, doc_type: str | None = None):
    stmt = select(Document).order_by(Document.created_at.desc())
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "",
    response_model=DocumentOut,
    dependencies=[Depends(require_permission(Perm.CREATE_CARD))],
    summary="Создание документа",
)
async def create_document(
    payload: DocumentCreate,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    doc_number = await _next_doc_number(db, payload.doc_type)
    doc = Document(
        doc_number=doc_number,
        doc_type=payload.doc_type,
        title=payload.title,
        description=payload.description,
        asset_id=payload.asset_id,
        inventory_id=payload.inventory_id,
        write_off_id=payload.write_off_id,
        repair_id=payload.repair_id,
        created_by_id=user.id,
    )
    db.add(doc)
    await write_audit(
        db,
        user_id=user.id,
        action="CREATE",
        entity_type="document",
        entity_id=str(doc.id),
        new_value=doc_number,
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    await db.refresh(doc)
    return doc


@router.post(
    "/{doc_id}/upload",
    response_model=DocumentOut,
    dependencies=[Depends(require_permission(Perm.EDIT_CARD))],
    summary="Загрузка файла документа",
)
async def upload_document_file(
    doc_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    request: Request,
    file: UploadFile = File(...),
):
    doc = await _get_doc_or_404(db, doc_id)
    if doc.status == DocumentStatusEnum.APPROVED.value:
        raise HTTPException(
            status_code=400, detail="Утверждённый документ нельзя изменять"
        )

    rel_path, original_name, size = await save_upload(
        file,
        subdir=f"documents/{doc.id}",
        allowed_extensions=DOCUMENT_EXTENSIONS,
    )
    # Удаляем прежний файл, если был
    if doc.file_path:
        delete_file(doc.file_path)
    doc.file_path = rel_path
    doc.file_name = original_name
    doc.file_size = size
    doc.mime_type = file.content_type or media_type_for(rel_path)

    await write_audit(
        db,
        user_id=user.id,
        action="UPLOAD_FILE",
        entity_type="document",
        entity_id=str(doc.id),
        new_value=original_name,
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get(
    "/{doc_id}/download",
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Скачивание файла документа",
)
async def download_document_file(doc_id: uuid.UUID, db: DbSession):
    doc = await _get_doc_or_404(db, doc_id)
    if not doc.file_path:
        raise HTTPException(status_code=404, detail="Файл не загружен")
    path = resolve_path(doc.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(
        path,
        media_type=doc.mime_type or media_type_for(doc.file_path),
        filename=doc.file_name or path.name,
    )


@router.get(
    "/{doc_id}",
    response_model=DocumentOut,
    dependencies=[Depends(require_permission(Perm.VIEW_CARDS))],
    summary="Документ по id",
)
async def get_document(doc_id: uuid.UUID, db: DbSession):
    return await _get_doc_or_404(db, doc_id)


@router.patch(
    "/{doc_id}",
    response_model=DocumentOut,
    dependencies=[Depends(require_permission(Perm.EDIT_CARD))],
    summary="Обновление документа",
)
async def update_document(
    doc_id: uuid.UUID,
    payload: DocumentUpdate,
    db: DbSession,
):
    doc = await _get_doc_or_404(db, doc_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(doc, field, value)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.post(
    "/{doc_id}/status",
    response_model=DocumentOut,
    dependencies=[Depends(require_permission(Perm.APPROVE_MOVE))],
    summary="Смена статуса документа",
)
async def change_status(
    doc_id: uuid.UUID,
    payload: StatusChangeRequest,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    doc = await _get_doc_or_404(db, doc_id)
    if doc.status == DocumentStatusEnum.APPROVED.value:
        raise HTTPException(status_code=400, detail="Утверждённый документ нельзя менять")

    doc.status = payload.status
    doc.status_changed_by_id = user.id
    doc.status_changed_at = datetime.now(timezone.utc)

    await write_audit(
        db,
        user_id=user.id,
        action="STATUS_CHANGE",
        entity_type="document",
        entity_id=str(doc.id),
        new_value=payload.status,
        comment=payload.comment,
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    await db.refresh(doc)
    return doc


@router.post(
    "/{doc_id}/sign",
    response_model=DocumentOut,
    dependencies=[Depends(require_permission(Perm.APPROVE_MOVE))],
    summary="Подписание документа",
)
async def sign_document(
    doc_id: uuid.UUID,
    payload: DocumentSignRequest,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    doc = await _get_doc_or_404(db, doc_id)
    doc.signer_user_id = user.id
    doc.signed_at = datetime.now(timezone.utc)
    doc.signer_role = "DIRECTOR"  # placeholder: роль подписанта

    await write_audit(
        db,
        user_id=user.id,
        action="SIGN",
        entity_type="document",
        entity_id=str(doc.id),
        comment=payload.comment,
        ip_address=_get_client_ip(request),
    )
    await db.commit()
    await db.refresh(doc)
    return doc