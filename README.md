# НАКС — виджет преквалификации (MVP)

Исследовательский MVP: встраиваемый через `<iframe>` веб-виджет опросника по
направлению «оборудование» для подготовки заявки на аттестацию сварочного
оборудования в НАКС. Контекст и правила проекта — `AGENTS.md`, спецификация —
`.scratch/naks-mvp-core/spec.md`.

Текущее состояние (тикет 01 «Каркас приложений и базовые контракты»):
типизированный каркас backend и frontend без бизнес-логики опросника —
health-эндпоинт, Pydantic-схемы будущих запросов/ответов, реестр АЦ, реестр
шаблонов и абстрактный `LLMProvider`, плюс тестовая инфраструктура для обоих
приложений. Сам опросник появится в тикете 02.

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

```bash
cd frontend
npm run dev
```

Vite поднимет dev-сервер (по умолчанию `http://localhost:5173`) и выведет
точный адрес в консоли.

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
