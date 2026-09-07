"""Сервис генерации отчётов.

Поддерживает форматы EXCEL, CSV, JSON, PDF.
Отчёты:
  - inventory_list   — инвентарная опись (список имущества)
  - asset_statement  — ведомость по местам хранения
  - discrepancies    — реестр расхождений по инвентаризации
  - write_off_act    — акт списания
"""

from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime
from io import BytesIO, StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Asset, Inventory, InventoryDiscrepancy, Room


async def _fetch_assets(db: AsyncSession, params: dict) -> list[dict]:
    stmt = select(Asset).order_by(Asset.inventory_number)
    if params.get("asset_type_id"):
        stmt = stmt.where(Asset.asset_type_id == uuid.UUID(str(params["asset_type_id"])))
    if params.get("room_id"):
        stmt = stmt.where(Asset.room_id == uuid.UUID(str(params["room_id"])))
    if params.get("status"):
        stmt = stmt.where(Asset.status == params["status"])
    result = await db.execute(stmt)
    rows = []
    for a in result.scalars().all():
        room = None
        if a.room_id:
            r = await db.get(Room, a.room_id)
            room = r.name if r else str(a.room_id)
        rows.append(
            {
                "Инвентарный номер": a.inventory_number,
                "Наименование": a.name,
                "Модель": a.model or "",
                "Серийный номер": a.serial_number or "",
                "Помещение": room or "",
                "Статус": a.status,
                "Кол-во": float(a.quantity) if a.quantity is not None else "",
                "Стоимость": float(a.cost) if a.cost is not None else "",
                "Год закупки": a.purchase_year or "",
            }
        )
    return rows


async def _fetch_discrepancies(db: AsyncSession, params: dict) -> list[dict]:
    inventory_id = params.get("inventory_id")
    if not inventory_id:
        return []
    result = await db.execute(
        select(InventoryDiscrepancy).where(
            InventoryDiscrepancy.inventory_id == uuid.UUID(str(inventory_id))
        )
    )
    rows = []
    for d in result.scalars().all():
        asset = await db.get(Asset, d.asset_id) if d.asset_id else None
        rows.append(
            {
                "Тип": d.discrepancy_type,
                "Имущество": asset.name if asset else "",
                "Инв. номер": asset.inventory_number if asset else "",
                "Учёт": float(d.accounting_quantity) if d.accounting_quantity is not None else "",
                "Факт": float(d.actual_quantity) if d.actual_quantity is not None else "",
                "Разница": float(d.difference) if d.difference is not None else "",
                "Статус": d.status,
            }
        )
    return rows


async def _fetch_write_off(db: AsyncSession, params: dict) -> list[dict]:
    # Акт списания: простой текстовый свод
    return [
        {
            "Акт списания": "",
            "Данные": "Формирование акта на основе карточки и причины списания",
        }
    ]


async def _generate_rows(db: AsyncSession, report_type: str, params: dict) -> list[dict]:
    if report_type in ("inventory_list", "asset_statement"):
        return await _fetch_assets(db, params)
    if report_type == "discrepancies":
        return await _fetch_discrepancies(db, params)
    if report_type == "write_off_act":
        return await _fetch_write_off(db, params)
    raise ValueError(f"Неизвестный тип отчёта: {report_type}")


def _build_excel(rows: list[dict]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Отчёт"
    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in rows:
            ws.append([row.get(h, "") for h in headers])
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _build_csv(rows: list[dict]) -> bytes:
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("")
    return output.getvalue().encode("utf-8-sig")


def _build_json(rows: list[dict]) -> bytes:
    return json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")


def _build_pdf(rows: list[dict]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    if rows:
        headers = list(rows[0].keys())
        data = [headers]
        for row in rows:
            data.append([row.get(h, "") for h in headers])
        table = Table(data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        elements.append(table)

    doc.build(elements)
    return buffer.getvalue()


def _save_result(data: bytes, fmt: str, job_id: uuid.UUID) -> str:
    """Сохраняет результат отчёта в файл, возвращает путь."""
    ext = {
        "EXCEL": "xlsx",
        "CSV": "csv",
        "JSON": "json",
        "PDF": "pdf",
    }.get(fmt, "bin")
    reports_dir = os.path.join(settings.upload_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"{job_id}.{ext}"
    path = os.path.join(reports_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


async def generate_report(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    report_type: str,
    fmt: str,
    params: dict | None,
) -> tuple[str, str | None]:
    """Генерирует отчёт. Возвращает (status, error_message)."""
    try:
        params = params or {}
        rows = await _generate_rows(db, report_type, params)
        if fmt == "EXCEL":
            data = _build_excel(rows)
        elif fmt == "CSV":
            data = _build_csv(rows)
        elif fmt == "JSON":
            data = _build_json(rows)
        elif fmt == "PDF":
            data = _build_pdf(rows)
        else:
            return "FAILED", f"Неподдерживаемый формат: {fmt}"
        path = _save_result(data, fmt, job_id)
        return "COMPLETED", None
    except Exception as exc:  # noqa: BLE001
        return "FAILED", str(exc)