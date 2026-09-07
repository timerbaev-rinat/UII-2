"""initial empty base revision

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-15

Базовая (корневая) ревизия Alembic. Модели данных добавляются
в Этапе 1 отдельными миграциями.

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass