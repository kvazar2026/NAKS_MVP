# НАКС — виджет преквалификации (MVP)

Исследовательский MVP: встраиваемый через `<iframe>` веб-виджет опросника по
направлению «оборудование» для подготовки заявки на аттестацию сварочного
оборудования в НАКС. Контекст и правила проекта — `AGENTS.md`, спецификация —
`.scratch/naks-mvp-core/spec.md`.

Текущее состояние (тикет 02 «Первый сквозной пользовательский сценарий»):
опросник по направлению «оборудование» работает целиком без iframe (прямой
URL виджета — iframe-встраивание появится в тикете 05) — заполнение формы →
`POST /api/v1/survey/validate` (структурная проверка → `MockProvider` →
повторная проверка нормализованных значений по справочникам) →
`POST /api/v1/documents/generate` (независимая повторная структурная
проверка, не доверяющая клиенту) → скачивание реального `.docx`. Ничего не
сохраняется на диске между запросами. Rate limiting, реальный
`AnthropicProvider`, черновые (warning) правила по чек-листу и
Playwright-e2e — в следующих тикетах.

## Структура репозитория

- `backend/` — FastAPI-приложение (Python).
- `frontend/` — React + TypeScript SPA-виджет (Vite), предназначен для
  встраивания через `<iframe>`.

## Backend

Проверено на Python 3.14.4; должно работать на Python 3.11+.

### Установка

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
```

`requirements.txt` — рантайм-зависимости, `requirements-dev.txt` — зависимости
для тестов (сам включает `requirements.txt`, поэтому одной установки
`requirements-dev.txt` достаточно и для запуска, и для тестов).

### Запуск

```bash
cd backend
.venv\Scripts\activate   # если ещё не активировано
uvicorn app.main:app --reload
```

Проверка: `GET http://127.0.0.1:8000/health` должен вернуть
`{"status": "ok"}`.

Демонстрационный `.docx`-шаблон (`backend/templates/demo_equipment_application.docx`,
единственная запись `template registry`) закоммичен как бинарный файл, но
его содержимое — читаемый Python-скрипт
`backend/scripts/generate_demo_template.py`; при необходимости изменить
текст/плейсхолдеры шаблона правьте скрипт и перегенерируйте файл:

```bash
cd backend
.venv\Scripts\activate
python scripts/generate_demo_template.py
```

### Тесты

```bash
cd backend
.venv\Scripts\activate   # если ещё не активировано
pytest
```

## Frontend

Проверено на Node.js 24.15.0.

### Установка

```bash
cd frontend
npm install
```

### Запуск

Виджет вызывает backend по относительным путям (`/api/v1/...`), поэтому для
рабочего сквозного сценария нужны оба процесса одновременно: backend
(`uvicorn`, см. выше, по умолчанию `http://127.0.0.1:8000`) и frontend.

```bash
cd frontend
npm run dev
```

Vite поднимет dev-сервер (по умолчанию `http://localhost:5173`) и выведет
точный адрес в консоли. Dev-сервер сам проксирует `/api/...` на backend
(`vite.config.ts`, `server.proxy`) — это тот же приём, что позже даст
reverse proxy в Docker Compose (тикет 07), поэтому CORS backend не
настраивает.

### Тесты

```bash
cd frontend
npm run test
```

Запускает `vitest run` (Vitest + React Testing Library).

## Запуск обоих тестовых наборов

```bash
cd backend && pytest
cd frontend && npm run test
```

Отдельного объединяющего скрипта в MVP пока нет — оба набора запускаются
независимо из каталогов `backend/` и `frontend/`.

## Docker

Одна команда через Docker Compose поднимает backend, frontend и reverse
proxy перед ними (nginx) — это даёт единый origin для локальной проверки
сценария встраивания через `<iframe>` (backend и frontend доступны через
один и тот же порт).

### Запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- `http://localhost:8080/` — виджет (frontend).
- `http://localhost:8080/health` — health-эндпоинт backend, должен вернуть
  `{"status": "ok"}`.
- `http://localhost:8080/api/v1/survey/validate`,
  `http://localhost:8080/api/v1/documents/generate` — публичные эндпоинты
  backend (тикет 02).

Порт `8080` настраивается переменной `PROXY_PORT` в `.env`. Наружу
опубликован только `proxy` — у backend и frontend есть собственные
healthcheck'и внутри Docker Compose (видны в `docker compose ps` как
`healthy`), но их порты сознательно не публикуются на хост, чтобы локальная
топология совпадала с той, что позже увидит rate limiting (тикет 06) за
настоящим reverse proxy.

Остановить стек: `docker compose down`.

### Переменные окружения

Все переменные окружения, нужные compose-стеку на данный момент,
задокументированы в `.env.example`. **Каждый следующий тикет, добавляющий
новую переменную backend или frontend, обязан дополнить `.env.example`**
соответствующей записью с описанием — без правки `docker-compose.yml`, так
как backend уже получает всё содержимое `.env` целиком через `env_file`.

### Деплой на свой сервер позже

В рамках MVP реального публичного/staging-деплоя нет — только локальный
Docker Compose (см. выше). Инструкция «как задеплоить этот же стек на
собственный сервер, когда это понадобится» — `docs/deployment.md`.
