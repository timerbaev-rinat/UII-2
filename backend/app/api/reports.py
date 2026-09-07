"""Эндпоинты отчётов (Этап 9).

- Постановка задач генерации отчётов в очередь (report_jobs)
- Получение статуса и результата
- Скачивание сформированного файла
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, Perm, require_permission
from app.models import ReportJob
from app.schemas.report import ReportCreate, ReportJobOut
from app.services.audit import write_audit
from app.services.reporting import generate_report

router = APIRouter()


@router.get(
    "",
    response_model=list[ReportJobOut],
    dependencies=[Depends(require_permission(Perm.VIEW_REPORTS))],
    summary="Список задач генерации отчётов",
)
async def list_reports(db: DbSession, status_filter: str | None = Query(default=None, alias="status")):
    stmt = select(ReportJob).order_by(ReportJob.created_at.desc())
    if status_filter:
        stmt = stmt.where(ReportJob.status == status_filter)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "",
    response_model=ReportJobOut,
    dependencies=[Depends(require_permission(Perm.VIEW_REPORTS))],
    summary="Запуск генерации отчёта",
)
async def create_report(
    payload: ReportCreate,
    db: DbSession,
    user: CurrentUser,
):
    job = ReportJob(
        report_type=payload.report_type,
        format=payload.format,
        params=payload.params,
        schedule_cron=payload.schedule_cron,
        created_by_id=user.id,
    )
    db.add(job)
    await db.flush()

    # Синхронная генерация (для простоты; в проде — через очередь)
    status, error = await generate_report(
        db,
        job_id=job.id,
        report_type=payload.report_type,
        fmt=payload.format,
        params=payload.params,
    )
    job.status = status
    job.error_message = error
    job.started_at = datetime.now(timezone.utc)
    job.completed_at = datetime.now(timezone.utc)

    await write_audit(
        db,
        user_id=user.id,
        action="REPORT",
        entity_type="report",
        entity_id=str(job.id),
        new_value=f"{payload.report_type} / {payload.format}",
    )
    await db.commit()
    await db.refresh(job)
    return job


@router.get(
    "/{job_id}",
    response_model=ReportJobOut,
    dependencies=[Depends(require_permission(Perm.VIEW_REPORTS))],
    summary="Статус задачи отчёта",
)
async def get_report(job_id: uuid.UUID, db: DbSession):
    job = await db.get(ReportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Задача отчёта не найдена")
    return job


@router.get(
    "/{job_id}/download",
    dependencies=[Depends(require_permission(Perm.VIEW_REPORTS))],
    summary="Скачивание готового отчёта",
)
async def download_report(job_id: uuid.UUID, db: DbSession):
    job = await db.get(ReportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Задача отчёта не найдена")
    if job.status != "COMPLETED" or not job.result_path:
        raise HTTPException(status_code=400, detail="Отчёт ещё не готов")
    if not os.path.exists(job.result_path):
        raise HTTPException(status_code=404, detail="Файл отчёта не найден")

    ext = {
        "EXCEL": "xlsx",
        "CSV": "csv",
        "JSON": "json",
        "PDF": "pdf",
    }.get(job.format, "bin")
    filename = f"report_{job.id}.{ext}"
    return FileResponse(job.result_path, filename=filename)