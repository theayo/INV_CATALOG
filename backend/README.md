# INVIX backend

FastAPI, каталог и обработчики aiogram. Точка входа ASGI — `app.main:app`.
Файл `server.py` экспортирует тот же объект для Vercel.

Из этой папки:

```sh
uv sync --locked
uv run python -m app.db.migrate
uv run python -m app.storage.minio
uv run uvicorn app.main:app --reload
```

- Проверка процесса: <http://localhost:8000/health>
- Swagger: <http://localhost:8000/docs>

Настройки читаются из переменных окружения, корневого `.env` и локального
`backend/.env`. Пример настроек находится в корне проекта.

`/health` проверяет доступность самого API. Для товаров нужны настроенные
PostgreSQL и MinIO. Полная настройка бота, ролей и webhook — в корневом README.

`GET /api/products` и `GET /api/products/{id}/image` публичны.
`POST /api/products` принимает multipart `title` + `photo`, проверяет подпись
`X-Telegram-Init-Data`, срок данных и роль администратора в PostgreSQL.
Бот использует тот же сервис каталога с Telegram ID из проверенного webhook.

Проверки: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`.
Для SQL-проверок задайте `TEST_DATABASE_URL`: тесты создают отдельные временные
схемы и удаляют только их, без очистки существующих таблиц.
