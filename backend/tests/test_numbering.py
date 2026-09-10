"""Юнит-тесты правил нумерации (генерация инвентарных номеров)."""

from app.services.numbering import (
    DEFAULT_TEMPLATE,
    _render,
    _safe_filename_template,
)


def test_default_template_when_none():
    assert _safe_filename_template(None) == DEFAULT_TEMPLATE
    assert _safe_filename_template("") == DEFAULT_TEMPLATE


def test_render_substitutes_placeholders():
    result = _render("{Год}-{Тип}-{№}", year=2026, type_code="EQP", seq=7)
    assert result == "2026-EQP-7"


def test_render_custom_template():
    result = _render("T{Тип}/{№}/{Год}", year=2025, type_code="FUR", seq=3)
    assert result == "TFUR/3/2025"