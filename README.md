# Система учёта имущества школы (PWA + Инвентаризация)

Строгий учёт имущества школы для муниципалитета: карточки имущества, инвентаризация
со смартфона (PWA), отчёты и выгрузки в Excel/CSV/JSON, аудит, роли и права.

## Стек

- **Бэкенд:** Python 3.11/3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **БД:** PostgreSQL 16
- **Фронтенд:** Vue 3 + Vite + TypeScript + Pinia + Vue Router (SPA)
- **PWA:** Vite PWA plugin (service worker, офлайн-кеш, манифест)
- **Отчёты:** pandas + openpyxl (Excel), reportlab (PDF), CSV/JSON
- **Инфраструктура:** Docker + docker-compose (Postgres, backend, frontend, nginx)

## Быстрый старт (Docker)

```bash
# 1. Скопировать конфигурацию и задать секреты
cp .env.example .env
# отредактировать .env (задать надёжные пароли)

# 2. Запустить все сервисы
docker compose up --build

# 3. Открыть приложение
#    Фронтенд + API через nginx: http://localhost:8080
#    API Swagger:                http://localhost:8080/api/docs
```

## Локальная разработка без Docker

Требования: Python 3.11+, Node 18+, PostgreSQL 16 локально.

### Бэкенд

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows (cmd)
pip install -r requirements.txt
# настроить DATABASE_URL в .env (host=localhost)
alembic upgrade head
uvicorn app.main:app --reload
```

### Фронтенд

```bash
cd frontend
npm install
npm run dev
```

## Безопасность, бэкапы и деплой

- **Заголовки безопасности/CSP**, **HttpOnly-кука** для refresh-токена,
  **валидация загрузок** (тип/размер/magic-bytes), структурированное логирование.
- **Автоматический бэкап БД** по расписанию (сервис `backup`,
  pg_dump → gzip → том `backups`), скрипты `scripts/backup.sh` / `scripts/restore.sh`.
- **HTTPS** — образец конфигурации `nginx/nginx.https.conf`.

Полная инструкция по эксплуатации — [`docs/operations.md`](docs/operations.md).
Руководство пользователя (роли, работа на ПК и смартфоне) — [`docs/user-guide.md`](docs/user-guide.md).

## Структура репозитория

```
├── backend/        # FastAPI-приложение
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── ...
│   ├── alembic/    # миграции БД
│   └── Dockerfile
├── frontend/       # Vue 3 SPA + PWA
│   └── ...
├── nginx/          # конфигурация reverse-proxy
├── docker-compose.yml
└── .env.example
```

Подробный план реализации — [`plans/implementation_plan.md`](plans/implementation_plan.md).