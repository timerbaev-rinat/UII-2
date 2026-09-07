"""create all tables

Revision ID: 0002_create_all_tables
Revises: 0001_initial
Create Date: 2026-08-16

Создание всех таблиц по модели данных (Этап 1).

Из-за циклических внешних ключей (documents <-> write_offs/repairs,
inventories, asset_moves, inventory_discrepancies) часть FK добавляется
отдельно после создания всех таблиц.

Revision identifiers.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_all_tables"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_pk() -> list[sa.Column]:
    return [
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
    ]


def _created() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _gen() -> str:
    import uuid
    return str(uuid.uuid4())


def upgrade() -> None:
    # gen_random_uuid доступна в PostgreSQL 13+ (pgcrypto не обязательна).
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ================= справочники =================
    op.create_table(
        "asset_statuses",
        *_uuid_pk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_created(),
    )
    op.create_unique_constraint("uq_asset_status_code", "asset_statuses", ["code"])

    op.create_table(
        "units_of_measure",
        *_uuid_pk(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("abbreviation", sa.String(16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_created(),
    )
    op.create_unique_constraint("uq_unit_code", "units_of_measure", ["code"])

    op.create_table(
        "materials",
        *_uuid_pk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_created(),
    )
    op.create_unique_constraint("uq_material_code", "materials", ["code"])

    # ================= пользователи, роли, права =================
    op.create_table(
        "users",
        *_uuid_pk(),
        sa.Column("login", sa.String(64), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_created(),
    )
    op.create_unique_constraint("uq_users_login", "users", ["login"])
    op.create_index("ix_users_login", "users", ["login"])

    op.create_table(
        "roles",
        *_uuid_pk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_created(),
    )
    op.create_unique_constraint("uq_roles_code", "roles", ["code"])
    op.create_index("ix_roles_code", "roles", ["code"])

    op.create_table(
        "permissions",
        *_uuid_pk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_created(),
    )
    op.create_unique_constraint("uq_permissions_code", "permissions", ["code"])
    op.create_index("ix_permissions_code", "permissions", ["code"])

    op.create_table(
        "user_roles",
        *_uuid_pk(),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
    )
    op.create_unique_constraint("uq_user_role", "user_roles", ["user_id", "role_id"])

    op.create_table(
        "role_permissions",
        *_uuid_pk(),
        sa.Column("role_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
    )
    op.create_unique_constraint("uq_role_permission", "role_permissions", ["role_id", "permission_id"])

    op.create_table(
        "delegations",
        *_uuid_pk(),
        sa.Column("delegator_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delegatee_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_code", sa.String(64), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_created(),
        sa.ForeignKeyConstraint(["delegator_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["delegatee_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ================= структура =================
    op.create_table(
        "buildings",
        *_uuid_pk(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("building_code", sa.String(32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_created(),
    )

    op.create_table(
        "rooms",
        *_uuid_pk(),
        sa.Column("building_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("room_number", sa.String(32), nullable=True),
        sa.Column("room_type", sa.String(64), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rooms_building_id", "rooms", ["building_id"])
    op.create_index("ix_rooms_room_number", "rooms", ["room_number"])

    # ================= имущество =================
    op.create_table(
        "asset_types",
        *_uuid_pk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("number_template", sa.String(255), nullable=True),
        *_created(),
    )
    op.create_unique_constraint("uq_asset_types_code", "asset_types", ["code"])

    op.create_table(
        "asset_attributes",
        *_uuid_pk(),
        sa.Column("asset_type_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("value_type", sa.String(32), nullable=False, server_default="string"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_created(),
        sa.ForeignKeyConstraint(["asset_type_id"], ["asset_types.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_asset_attributes_asset_type_id", "asset_attributes", ["asset_type_id"])

    op.create_table(
        "assets",
        *_uuid_pk(),
        sa.Column("inventory_number", sa.String(64), nullable=False),
        sa.Column("asset_type_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("serial_number", sa.String(255), nullable=True),
        sa.Column("purchase_year", sa.Integer(), nullable=True),
        sa.Column("commissioning_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="IN_STOCK"),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("material", sa.String(255), nullable=True),
        sa.Column("cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("write_off_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("photo_path", sa.String(512), nullable=True),
        sa.Column("custom_attributes", sa.JSON(), nullable=True),
        sa.Column("responsible_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["asset_type_id"], ["asset_types.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["responsible_user_id"], ["users.id"]),
    )
    op.create_unique_constraint("uq_asset_inventory_number", "assets", ["inventory_number"])
    op.create_index("ix_assets_inventory_number", "assets", ["inventory_number"])
    op.create_index("ix_assets_asset_type_id", "assets", ["asset_type_id"])
    op.create_index("ix_assets_room_id", "assets", ["room_id"])
    op.create_index("ix_assets_status", "assets", ["status"])
    op.create_index("ix_assets_serial_number", "assets", ["serial_number"])

    op.create_table(
        "asset_number_reservations",
        *_uuid_pk(),
        sa.Column("inventory_number", sa.String(64), nullable=False),
        sa.Column("asset_type_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reserved_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["asset_type_id"], ["asset_types.id"]),
        sa.ForeignKeyConstraint(["reserved_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
    )
    op.create_unique_constraint("uq_asset_number_reservation", "asset_number_reservations", ["inventory_number"])

    # ================= операции (без FK на documents — добавятся позже) =================
    op.create_table(
        "asset_moves",
        *_uuid_pk(),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_room_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_room_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("moved_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("document_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["to_room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["moved_by_id"], ["users.id"]),
    )
    op.create_index("ix_asset_moves_asset_id", "asset_moves", ["asset_id"])

    op.create_table(
        "write_offs",
        *_uuid_pk(),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("commission_members", sa.Text(), nullable=True),
        sa.Column("write_off_date", sa.Date(), nullable=True),
        sa.Column("document_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("status_changed_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["status_changed_by_id"], ["users.id"]),
    )
    op.create_index("ix_write_offs_asset_id", "write_offs", ["asset_id"])

    op.create_table(
        "repairs",
        *_uuid_pk(),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contractor", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column("is_guarantee", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("act_number", sa.String(64), nullable=True),
        sa.Column("document_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        *_created(),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
    )
    op.create_index("ix_repairs_asset_id", "repairs", ["asset_id"])

    op.create_table(
        "issuances",
        *_uuid_pk(),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issued_to_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issued_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_return", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("returned_condition", sa.Text(), nullable=True),
        sa.Column("is_returned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        *_created(),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issued_to_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["issued_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
    )
    op.create_index("ix_issuances_asset_id", "issuances", ["asset_id"])

    # ================= инвентаризация =================
    op.create_table(
        "inventories",
        *_uuid_pk(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("inv_type", sa.String(32), nullable=False, server_default="PLANNED"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("coverage", sa.String(64), nullable=True),
        sa.Column("commission", sa.Text(), nullable=True),
        sa.Column("building_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("room_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"]),
    )
    op.create_index("ix_inventories_status", "inventories", ["status"])

    op.create_table(
        "inventory_items",
        *_uuid_pk(),
        sa.Column("inventory_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accounting_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("accounting_status", sa.String(32), nullable=True),
        sa.Column("actual_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_status", sa.String(32), nullable=True),
        sa.Column("actual_condition", sa.Text(), nullable=True),
        sa.Column("photo_path", sa.String(512), nullable=True),
        sa.Column("is_checked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("checked_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["checked_by_id"], ["users.id"]),
    )
    op.create_unique_constraint("uq_inventory_asset", "inventory_items", ["inventory_id", "asset_id"])
    op.create_index("ix_inventory_items_inventory_id", "inventory_items", ["inventory_id"])

    op.create_table(
        "inventory_discrepancies",
        *_uuid_pk(),
        sa.Column("inventory_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("discrepancy_type", sa.String(32), nullable=False),
        sa.Column("accounting_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("difference", sa.Numeric(12, 3), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("responsible_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("document_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["responsible_user_id"], ["users.id"]),
    )
    op.create_index("ix_inventory_discrepancies_inventory_id", "inventory_discrepancies", ["inventory_id"])

    # ================= документы (после всех, т.к. ссылается на операции) =================
    op.create_table(
        "documents",
        *_uuid_pk(),
        sa.Column("doc_number", sa.String(64), nullable=False),
        sa.Column("doc_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("signer_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signer_role", sa.String(64), nullable=True),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("inventory_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("write_off_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("repair_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("status_changed_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["signer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventories.id"]),
        sa.ForeignKeyConstraint(["write_off_id"], ["write_offs.id"]),
        sa.ForeignKeyConstraint(["repair_id"], ["repairs.id"]),
        sa.ForeignKeyConstraint(["status_changed_by_id"], ["users.id"]),
    )
    op.create_index("ix_documents_doc_number", "documents", ["doc_number"])

    # ================= аудит =================
    op.create_table(
        "audit_log",
        *_uuid_pk(),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("field_name", sa.String(128), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"])
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # ================= отчёты =================
    op.create_table(
        "report_jobs",
        *_uuid_pk(),
        sa.Column("report_type", sa.String(64), nullable=False),
        sa.Column("format", sa.String(16), nullable=False, server_default="EXCEL"),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("result_path", sa.String(512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("schedule_cron", sa.String(128), nullable=True),
        *_created(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
    )
    op.create_index("ix_report_jobs_report_type", "report_jobs", ["report_type"])
    op.create_index("ix_report_jobs_status", "report_jobs", ["status"])

    # ================= добавление отложенных FK (циклические связи) =================
    op.create_foreign_key(
        "fk_asset_moves_document", "asset_moves", "documents", ["document_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_write_offs_document", "write_offs", "documents", ["document_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_repairs_document", "repairs", "documents", ["document_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_inventory_discrepancies_document",
        "inventory_discrepancies", "documents", ["document_id"], ["id"],
    )

    # ================= базовые справочники (наполнение) =================
    statuses = sa.table(
        "asset_statuses",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
    )
    op.bulk_insert(
        statuses,
        [
            {"id": _gen(), "code": "IN_STOCK", "name": "На учёте"},
            {"id": _gen(), "code": "ON_REPAIR", "name": "В ремонте"},
            {"id": _gen(), "code": "WRITTEN_OFF", "name": "Списано"},
        ],
    )
    units = sa.table(
        "units_of_measure",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("abbreviation", sa.String),
    )
    op.bulk_insert(
        units,
        [
            {"id": _gen(), "code": "PIECE", "name": "Штука", "abbreviation": "шт."},
            {"id": _gen(), "code": "SET", "name": "Комплект", "abbreviation": "компл."},
            {"id": _gen(), "code": "KG", "name": "Килограмм", "abbreviation": "кг"},
            {"id": _gen(), "code": "METER", "name": "Метр", "abbreviation": "м"},
        ],
    )


def downgrade() -> None:
    # Порядок удаления обратный созданию (сначала FK, затем таблицы).
    op.drop_constraint("fk_inventory_discrepancies_document", "inventory_discrepancies", type_="foreignkey")
    op.drop_constraint("fk_repairs_document", "repairs", type_="foreignkey")
    op.drop_constraint("fk_write_offs_document", "write_offs", type_="foreignkey")
    op.drop_constraint("fk_asset_moves_document", "asset_moves", type_="foreignkey")

    op.drop_table("report_jobs")
    op.drop_table("audit_log")
    op.drop_table("documents")
    op.drop_table("inventory_discrepancies")
    op.drop_table("inventory_items")
    op.drop_table("inventories")
    op.drop_table("issuances")
    op.drop_table("repairs")
    op.drop_table("write_offs")
    op.drop_table("asset_moves")
    op.drop_table("asset_number_reservations")
    op.drop_table("assets")
    op.drop_table("asset_attributes")
    op.drop_table("asset_types")
    op.drop_table("rooms")
    op.drop_table("buildings")
    op.drop_table("delegations")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("materials")
    op.drop_table("units_of_measure")
    op.drop_table("asset_statuses")