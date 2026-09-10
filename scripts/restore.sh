#!/usr/bin/env sh
# Восстановление БД из архивной копии, созданной backup.sh.
#
# Использование:
#   RESTORE_FILE=/backups/asset_school_20260101_120000.sql.gz ./scripts/restore.sh
#
# ВНИМАНИЕ: восстановление перезаписывает текущую базу. Делайте бэкап перед ним.
#
# Требуемые переменные окружения:
#   POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
#   RESTORE_FILE (путь к .sql.gz)

set -eu

DB_NAME="${POSTGRES_DB:?POSTGRES_DB не задан}"
DB_USER="${POSTGRES_USER:?POSTGRES_USER не задан}"
DB_PASS="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD не задан}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
RESTORE_FILE="${RESTORE_FILE:?RESTORE_FILE не задан}"

if [ ! -f "$RESTORE_FILE" ]; then
    echo "[restore] Файл не найден: $RESTORE_FILE" >&2
    exit 1
fi

export PGPASSWORD="$DB_PASS"

echo "[restore] Проверка архива: $RESTORE_FILE"
pg_restore --list "$RESTORE_FILE" > /dev/null 2>&1 \
    || { echo "[restore] Архив повреждён!" >&2; exit 1; }

echo "[restore] Восстановление в $DB_NAME ..."
gunzip -c "$RESTORE_FILE" | pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists

echo "[restore] Завершено."