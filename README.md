# INV_CATALOG

Каталог товаров: администратор добавляет фото с названием через Telegram-бота,
пользователь смотрит товары в браузере или Mini App.

Next.js App Router, FastAPI, aiogram 3, PostgreSQL и MinIO.

## Запуск

Нужны Node.js 24, Python 3.12, uv, PostgreSQL и MinIO.
Настройки backend — в корневом `.env` или `backend/.env`.

```powershell
Copy-Item .env.example .env
cd backend
uv sync --locked
uv run python -m app.db.migrate
uv run python -m app.storage.minio
uv run uvicorn app.main:app --reload
```

Перед запуском заполни `.env`:

| Переменная | Значение |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL; для Neon — pooled URL с `sslmode=require` |
| `MINIO_ENDPOINT` | S3 API без схемы, например `storage.example.com:443` |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Ключи MinIO |
| `MINIO_BUCKET` | Bucket для фото, по умолчанию `product-photos` |
| `MINIO_SECURE` | `true` для HTTPS, `false` локально |
| `BOT_TOKEN` | Токен из BotFather |
| `DEMO_ADMIN_CODE` | Код входа администратора |
| `TELEGRAM_WEBHOOK_SECRET` | Секрет webhook: буквы, цифры, `_` и `-` |
| `WEB_APP_URL` | Публичный HTTPS-адрес каталога для Mini App |

Миграция пропускает уже применённые файлы. Bucket создаётся, если его ещё нет.
Пароли в `.env.example` предназначены для локального запуска.

Frontend запусти из корня проекта в другом терминале:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

`API_BASE_URL` в `frontend/.env.local` — адрес backend, локально
`http://localhost:8000`. Каталог: `http://localhost:3000`, Swagger:
`http://localhost:8000/docs`. `/health` проверяет доступность процесса API.

## Бот

Для локальной разработки, из `backend`:

```powershell
uv run python -m app.bot.manage poll
```

Polling удаляет webhook, сохраняя ожидающие события. Запускается одним процессом.
После размещения backend переключи бота на webhook:

```powershell
uv run python -m app.bot.manage webhook --url https://your-api.vercel.app
```

Команда настраивает меню и endpoint `/api/telegram/webhook`.
Для Mini App нужен HTTPS `WEB_APP_URL`. Демокод передаётся проверяющему отдельно.

Проверка демо:

1. `/start` — обычный пользователь, кнопки Mini App и браузера.
2. `/admin <демокод>` — роль администратора. Неверный код роль не меняет.
3. «Создать товар» или `/create` — отправь одно фото с названием в подписи.
4. Открой каталог или нажми «Обновить».
5. `/user` — создание снова недоступно. Повторный `/start` сохраняет роль.

Название — от 1 до 200 символов. Фото — JPEG, PNG или WebP до 10 МБ и
20 мегапикселей. Альбомы не поддерживаются. Просмотр каталога публичный.

## Устройство

- `backend/app/api` — HTTP-маршруты и проверка Telegram-авторизации.
- `backend/app/bot` — обработчики, polling и настройка webhook.
- `backend/app/catalog.py` — создание и чтение товаров.
- `backend/app/db`, `backend/migrations` — PostgreSQL и миграции.
- `backend/app/storage` — MinIO.
- `frontend/src/app` — каталог, Mini App SDK и выдача фотографий.
- `backend/tests` — проверки API, бота, валидации и SQL.

`GET /api/products` и `GET /api/products/{id}/image` публичны.
`POST /api/products` принимает multipart `title` и `photo`; требует подписанные
данные `X-Telegram-Init-Data` и роль admin в БД. Бот использует тот же сервис
каталога. Фото выдаются через API, bucket остаётся закрытым.

В PostgreSQL сохраняются товары, Telegram ID, роли и ключи обработанных сообщений.
Повторная доставка фото не создаёт второй товар. FSM не используется: фото и
название приходят одним сообщением. Все экземпляры используют общие хранилища.

Два процесса backend: `uv run uvicorn app.main:app --workers 2`.
Два frontend после `npm run build`: `npm start -- --port 3000` и
`npm start -- --port 3001`, с одинаковым `API_BASE_URL`.
Webhook направляется через общую маршрутизацию, polling для реплик не подходит.

При ошибке SQL-вставки новое фото удаляется. При неизвестном результате COMMIT
фото остаётся: возможен лишний объект, зато не удаляется фото сохранённого товара.

## Проверки

Из `backend`: `uv run pytest -q`, `uv run ruff check .`,
`uv run ruff format --check .`.
SQL-тесты требуют `TEST_DATABASE_URL`: они создают и удаляют собственные временные
схемы. Без подключения эти тесты пропускаются.

Из `frontend`: `npm run lint`, `npm run typecheck`, `npm run build`.
GitHub Actions запускает эти проверки при push в `main` и pull request.
Проверка контейнеров включается вручную через Run workflow → `docker`.

## Docker

Из корня, с настроенным `.env`:

```powershell
docker compose up --build -d
docker compose exec backend python -m app.db.migrate
```

Порты: frontend — 3000, backend — 8000, PostgreSQL — 5432,
MinIO API — 9000, MinIO Console — 9001. `minio-init` создаёт bucket и завершается
с кодом 0. Данные остаются в томах после `docker compose down`.
Для разработки можно поднять только хранилища:
`docker compose up -d postgres minio minio-init`.
При изменении портов или паролей обнови адреса и `DATABASE_URL` в `.env`.

Образы MinIO и mc собираются из исходников; первая сборка может занять несколько
минут. Версии закреплены в `infra/minio/Dockerfile`:
[MinIO](https://github.com/minio/minio/tree/RELEASE.2025-10-15T17-29-55Z) и
[mc](https://github.com/minio/mc/tree/RELEASE.2025-08-13T08-35-41Z).
Лицензия обоих проектов — AGPL-3.0, её копии включены в образы.

## Размещение

Для Vercel — два проекта с Root Directory `frontend` и `backend`.
В backend настраиваются PostgreSQL, MinIO и Telegram, в frontend — `API_BASE_URL`.
После создания хранилищ примени миграцию, создай bucket и включи webhook.
При запуске serverless-функций миграции автоматически не выполняются.
Docker включает standalone-сборку через `NEXT_STANDALONE=1`;
обычный `npm run build` готовит frontend для `npm start`.
