# INVIX frontend

Next.js App Router, TypeScript и ESLint. Стартовая страница находится в
`src/app/page.tsx`, общие стили — в `src/app/globals.css`.

## Разработка

Нужен Node.js 24. Из этой папки:

```powershell
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Приложение доступно по адресу <http://localhost:3000>.
`API_BASE_URL` задает адрес FastAPI для серверных запросов. Страница запрашивает
актуальные товары, показывает пустой каталог или ошибку загрузки. Фото проходят
через `/images/[id]`, поэтому браузеру не нужен прямой доступ к MinIO.
Telegram SDK подключен для открытия этой же страницы внутри Mini App.

## Проверки

```powershell
npm run lint
npm run typecheck
npm run build
```

Dockerfile включает standalone-сборку через `NEXT_STANDALONE=1`. Обычный
`npm run build` готовит приложение для `npm start`. Общий запуск с backend,
PostgreSQL и MinIO описан в корневом `README.md`.
При размещении на Vercel корневая папка этого приложения — `frontend`.
