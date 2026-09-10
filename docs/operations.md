# Эксплуатация: безопасность, бэкапы, деплой (Этап 11)

## 1. Безопасность HTTP

Бэкенд автоматически добавляет заголовки безопасности через
[`SecurityHeadersMiddleware`](../backend/app/core/middleware.py):

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy`
- `Content-Security-Policy` (набор в зависимости от `STRICT_CSP`)
- `Strict-Transport-Security` (при `HSTS_ENABLED=true`)
- `Cache-Control: no-store` для `/auth*` и `/assets*`

Управление — переменные окружения (см. `.env.example`):

| Переменная | Значение | Описание |
|-----------|----------|----------|
| `ENV` | `production` | Включает prod-поведение |
| `SECURITY_HEADERS` | `true` | Заголовки безопасности |
| `STRICT_CSP` | `true` | Строгий CSP без inline |
| `HSTS_ENABLED` | `true` | Только при HTTPS |
| `ALLOWED_HOSTS` | домен | Whitelist хостов (TrustedHost) |

### Refresh-токен в HttpOnly-куке

При `COOKIE_NAME` непустом login/refresh дополнительно кладут refresh-токен в
HttpOnly-куку (`COOKIE_HTTPONLY`, `COOKIE_SECURE`, `COOKIE_SAMESITE`). При HTTPS
обязательно `COOKIE_SECURE=true`.

### Валидация входных данных и загрузки

- Pydantic-схемы валидируют все входные данные.
- Загрузка файлов: проверка расширения (whitelist), MIME-типа, максимального
  размера (`MAX_UPLOAD_SIZE_MB`) и **фактического формата изображений** по
  magic-bytes (защита от подмены расширения) — [`storage.py`](../backend/app/services/storage.py).
- Пути к файлам разрешаются с защитой от path traversal.

## 2. Логирование и мониторинг

- Структурированное логирование настроено в [`middleware.py`](../backend/app/core/middleware.py)
  (`setup_logging`), уровень — `LOG_LEVEL`.
- Каждый запрос пишется в лог: метод, путь, статус, длительность.
- Глобальный обработчик ошибок логирует стек, клиенту отдаёт общее сообщение
  (без раскрытия деталей).
- Эндпоинт `/health` (через nginx: `/api/health`) — базовый health-check.

Для внешнего мониторинга достаточно периодически опрашивать `/api/health` и
собирать логи контейнера `asset_backend`.

## 3. Резервное копирование

Автоматический бэкап БД по расписанию — сервис `backup` в `docker-compose.yml`
(образ `postgres:16-alpine`, pg_dump → gzip → том `backups`).

```bash
# Интервалы и хранение задаются в .env:
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=14

docker compose up -d   # сервис backup стартует автоматически
```

Ручной запуск:

```bash
BACKUP_DIR=/tmp/backups ./scripts/backup.sh
```

Архив: `asset_school_YYYYMMDD_HHMMSS.sql.gz` (custom format). После создания
выполняется проверка целостности через `pg_restore --list`.

> **Важно:** том `backups` расположен локально на сервере. Для защиты данных
> требуется регулярно выгружать архивы во внешнее хранилище (S3/NAS/др.), см.
> «Хранение вне сервера» ниже.

### Хранение вне сервера (рекомендация)

Раз в сутки копировать содержимое тома `backups` во внешний бэкспенс. Пример
(на хосте):

```bash
docker run --rm -v asset_backups:/data -v $PWD/offsite:/offsite \
  alpine sh -c "cp -r /data/. /offsite/"
```

### Восстановление (процедура)

```bash
RESTORE_FILE=/backups/asset_school_20260101_120000.sql.gz docker compose \
  -f docker-compose.yml run --rm backup /bin/sh -c \
  'chmod +x /scripts/restore.sh && /scripts/restore.sh'
```

`restore.sh` проверяет архив, пересоздаёт объекты (`--clean --if-exists`) и
загружает данные. **Восстановление перезаписывает базу** — перед ним обязателен
свежий бэкап. Рекомендуется регулярно выполнять тестовые восстановления в
отдельный экземпляр БД.

## 4. Деплой (production)

### Конфигурация

```bash
cp .env.example .env
# Обязательно заменить SECRET_KEY и пароли БД
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Продакшен-рекомендации для `.env`:
`ENV=production`, `STRICT_CSP=true`, `ALLOWED_HOSTS=<домен>`,
`COOKIE_SECURE=true`, `HSTS_ENABLED=true` (при HTTPS).

### HTTPS

- Использовать образец [`nginx/nginx.https.conf`](../nginx/nginx.https.conf):
  TLS 1.2/1.3, редирект 80→443, `/api` проксируется с обрезкой префикса.
- Сертификаты монтируются в контейнер (например, certbot).
- Открыть порт `443` в `docker-compose.yml` для nginx.

### Проверка перед запуском

```bash
docker compose config      # валидация compose
nginx -t                   # валидация конфига nginx (внутри контейнера)
docker compose up --build -d
```

После старта проверить: `/api/health`, `/api/docs`, вход через `/`.

## 5. Тестирование

Набор тестов — в [`../backend/tests`](../backend/tests): юнит- (безопасность,
нумерация, хранилище), интеграционные (auth, RBAC, полный сценарий
поступление→учёт→перемещение→инвентаризация→списание) и генерация отчётов.

Запуск (требуется работающий PostgreSQL):

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
# по умолчанию используется БД asset_school_test на localhost:5432;
# при необходимости задать: TEST_DATABASE_URL=postgresql+asyncpg://.../asset_school_test
pytest -v
```

Схема тестовой БД создаётся автоматически, данные между тестами изолируются
(TRUNCATE + повторный сидинг ролей). В `conftest.py` задаются тестовые
пользователи: `admin`, `zavhoz`, `director`, `muni` (пароль `pass123`).