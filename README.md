# INVIX Catalog

Базовый каркас каталога: Next.js App Router, FastAPI, aiogram, PostgreSQL и MinIO.
MVP: создание товара одним сообщением «фото + подпись» через Telegram-бота,
общий каталог в браузере и Telegram Mini App, роли пользователя и администратора.
Название и роль хранятся в PostgreSQL, фото — в закрытом bucket MinIO.

## Настройка MVP без Docker

Нужны Node.js 24, Python 3.12, `uv`, доступные PostgreSQL и MinIO.
Создайте `.env` из `.env.example`, если своего файла еще нет. Заполните:

| Переменная backend | Значение |
| --- | --- |
| `DATABASE_URL` | Строка подключения PostgreSQL; для Neon — pooled URL с `sslmode=require` |
| `MINIO_ENDPOINT` | Адрес S3 API без схемы, например `storage.example.com:443` |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Ключи MinIO |
| `MINIO_BUCKET` | По умолчанию `product-photos` |
| `MINIO_SECURE` | `true` для HTTPS, `false` локально |
| `BOT_TOKEN` | Токен бота из BotFather |
| `DEMO_ADMIN_CODE` | Собственный демокод для `/admin`; передается проверяющему отдельно |
| `TELEGRAM_WEBHOOK_SECRET` | Случайная строка из букв, цифр, `_` и `-` для webhook |
| `WEB_APP_URL` | Публичный HTTPS-адрес frontend для Mini App |

Затем из `backend`:

```powershell
uv sync --locked
uv run python -m app.db.migrate
uv run python -m app.storage.minio
uv run uvicorn app.main:app --reload
```

Миграция повторяемая: уже примененные SQL-файлы пропускаются. Bucket создается,
если его еще нет. Настройки хранятся в корневом `.env` или `backend/.env`.

Из `frontend`:

```powershell
Copy-Item .env.example .env.local
npm ci
npm run dev
```

`API_BASE_URL` в `frontend/.env.local` — адрес backend, локально
`http://localhost:8000`. Эта переменная используется только сервером Next.js.
Каталог доступен по `http://localhost:3000`. Для Telegram нужен публичный HTTPS.

## Подключение бота

Для одного локального процесса можно использовать polling; команда удаляет
webhook, сохраняя ожидающие события. Не запускайте несколько poller одновременно.

```powershell
cd backend
uv run python -m app.bot.manage poll
```

После размещения backend включите webhook:

```powershell
uv run python -m app.bot.manage webhook --url https://your-api.vercel.app
```

Команда регистрирует команды бота, кнопку Mini App и webhook
`/api/telegram/webhook`. В окружении должны быть `BOT_TOKEN`,
`TELEGRAM_WEBHOOK_SECRET` и HTTPS `WEB_APP_URL`. Секрет проверяется до обработки
обновления. Событие обрабатывается целиком до ответа Telegram, без фоновых задач.

## Проверка демо

1. `/start` — сохраняет Telegram ID с ролью `user`, показывает «У меня есть товар»
   и кнопки открытия каталога в Mini App и браузере.
2. `/admin <демокод>` — сохраняет роль `admin`; неверный код роль не меняет.
3. «Создать товар» или `/create` — просит одно фото с названием в подписи.
4. Отправьте фото JPEG, PNG или WebP до 10 МБ, подпись от 1 до 200 символов.
   Альбомы не принимаются. Успех подтверждается после сохранения фото и записи.
5. Откройте каталог или нажмите «Обновить»: товар должен появиться с фотографией.
6. `/user` — сохраняет обычную роль и закрывает создание. Повторный `/start`
   сохраняет текущую роль. Устаревшая кнопка создания не обходит проверку прав.

Просмотр каталога публичный, Telegram-авторизация для него не требуется.
Создание через HTTP требует проверенной подписи Telegram Mini App и роли admin.
Сохранены только Telegram ID и роль, без профиля пользователя.

## Структура

```text
frontend/               Next.js, TypeScript, ESLint
  src/app/              Страницы App Router
backend/                Python 3.12, uv, FastAPI
  app/api/              HTTP-маршруты
  app/bot/              Модули aiogram
  app/db/               Место для PostgreSQL
  app/storage/          Место для MinIO
  migrations/           SQL-миграции и учет примененных версий
  tests/                Проверки API, бота, прав и PostgreSQL
  server.py             ASGI-вход для Vercel
compose.yaml            Локальный запуск и хранилища
infra/minio/            Сборка MinIO и mc из закрепленных исходников
.env.example            Пример локальной конфигурации
```

## Запуск всего проекта через Docker

Нужен запущенный Docker Desktop с Linux-контейнерами и Docker Compose v2.
В PowerShell из корня проекта:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec backend python -m app.db.migrate
```

| Сервис | Адрес |
| --- | --- |
| Каталог | <http://localhost:3000> |
| API health | <http://localhost:8000/health> |
| Swagger | <http://localhost:8000/docs> |
| MinIO API | <http://localhost:9000> |
| MinIO Console | <http://localhost:9001> |
| PostgreSQL | `localhost:5432`, база `invix` |

Локальные учетные данные PostgreSQL и MinIO приведены в `.env.example`.
Порты опубликованы только на `127.0.0.1`.
Одноразовый сервис `minio-init` ждет готовности MinIO и создает закрытый bucket
`product-photos`, если его еще нет. Успешное завершение этого сервиса с кодом 0
ожидаемо.

Официальные образы MinIO больше не доступны в Docker Hub, поэтому сервер и
клиент собираются из исходников. Первая сборка может занять несколько минут.
Версии и ссылки на исходники приведены в `infra/minio/README.md`.

PostgreSQL и MinIO хранят данные в именованных томах. Команда
`docker compose down` останавливает проект и сохраняет эти тома.

```powershell
docker compose ps -a
docker compose logs backend frontend
docker compose down
```

## Разработка приложений на компьютере

Нужны Node.js 24, Python 3.12 и [uv](https://docs.astral.sh/uv/).
Можно оставить в Docker только инфраструктуру:

```powershell
docker compose up -d postgres minio minio-init
```

В отдельном терминале запустить backend:

```powershell
cd backend
uv sync --locked
uv run uvicorn app.main:app --reload
```

В другом терминале запустить frontend:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Backend читает корневой `.env` или `backend/.env`; frontend — свой `.env.local`.
При смене локальных портов нужно обновить адреса в соответствующих настройках.
Если меняется пароль PostgreSQL для запуска на компьютере, нужно обновить и
`DATABASE_URL`.

## Проверки

Из `backend`:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Из `frontend`:

```powershell
npm run lint
npm run typecheck
npm run build
```

Из корня:

```powershell
docker compose config --quiet
```

GitHub Actions проверяет линтеры, типы, backend-тесты и сборку Next.js при push
в `main` и pull request. Полная проверка Docker-стека запускается только вручную
через Run workflow → `docker`. Действующие облачные ключи для CI не нужны.
SQL-тесты включаются при заданном `TEST_DATABASE_URL` и работают в собственных
временных схемах. Без строки подключения они явно пропускаются.

## Несколько экземпляров

Товары и роли не хранятся в памяти процесса. Обработчики бота не используют FSM:
сообщение photo + caption содержит все данные. Несколько backend используют один
webhook за маршрутизацией площадки, общие PostgreSQL и MinIO.

Для локальной проверки можно запустить backend с двумя процессами:

```powershell
cd backend
uv run uvicorn app.main:app --workers 2
```

Frontend после `npm run build` можно запустить из двух терминалов командами
`npm start -- --port 3000` и `npm start -- --port 3001`, с одинаковым
`API_BASE_URL`. Оба показывают один каталог. При раздельных backend-процессах
можно последовательно направить один и тот же webhook на каждый порт.
Повторная доставка того же сообщения с фото создает один товар: ключ события
сохранен в БД, а блокировка строки пользователя защищает от одновременной обработки.

Если SQL-вставка не удалась после загрузки фото, приложение удаляет новый объект.
Если результат COMMIT неизвестен из-за обрыва связи, фото сохраняется, чтобы не
удалить объект уже записанного товара; возможен лишний объект без записи.
Сервер не подтверждает успех при ошибке хранилища. Кластеры хранилищ и аварийные
испытания в MVP не входят.

## Последующее размещение

- Vercel Hobby: отдельные проекты с Root Directory `frontend` и `backend`.
- Neon Free: PostgreSQL, строка подключения в `DATABASE_URL` бэкенда.
- Northflank Developer Sandbox: MinIO с внешним TLS-адресом.
- Переменные Telegram и MinIO из `.env.example` настраиваются в backend.
- `API_BASE_URL` настраивается в frontend и указывает на production-адрес API.

После создания хранилищ примените миграцию и создайте bucket командами выше,
затем включите webhook. Автоматически при запуске serverless-функций миграции
не выполняются. Ссылки на работающие приложения появятся после размещения.

В облаке не нужны локальные переменные `POSTGRES_*` и `MINIO_ROOT_*` из Compose.
Рабочие ключи хранилища задаются через `MINIO_ACCESS_KEY` и `MINIO_SECRET_KEY`.
`MINIO_ENDPOINT` — адрес API в формате `host:port` без `https://`;
для облачного HTTPS-подключения `MINIO_SECURE=true`.

`.env`, токены и локальные виртуальные окружения исключены из Git.
Значения `*_dev_*` предназначены для локального запуска.
