#!/usr/bin/env sh
# Резервное копирование PostgreSQL (pg_dump) в сжатый архив.
#
# Использование:
#   BACKUP_DIR=/backups RETENTION_DAYS=14 ./scripts/backup.sh
# Или через docker-compose (сервис backup, см. docker-compose.yml).
#
# Требуемые переменные окружения:
#   POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
# Опционально: BACKUP_DIR (по умолчанию /backups), RETENTION_DAYS (по умолчанию 14)

set -eu

DB_NAME="${POSTGRES_DB:?POSTGRES_DB не задан}"
DB_USER="${POSTGRES_USER:?POSTGRES_USER не задан}"
DB_PASS="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD не задан}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$BACKUP_DIR/${DB_NAME}_${STAMP}.sql.gz"

# pg_dump без интерактивного ввода пароля
export PGPASSWORD="$DB_PASS"

echo "[backup] Старт: $FILE"
pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --no-owner \
    --no-acl \
    | gzip > "$FILE"

SIZE=$(du -h "$FILE" | cut -f1)
echo "[backup] Готово: $FILE ($SIZE)"

# Удаление старых архивов
echo "[backup] Удаление архивов старше ${RETENTION_DAYS} дн."
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

# Проверка целостности последнего архива
if pg_restore --list "$FILE" > /dev/null 2>&1; then
    echo "[backup] Целостность подтверждена."
else
    echo "[backup] ОШИБКА: архив повреждён!" >&2
    exit 1
fi

echo "[backup] Завершено."