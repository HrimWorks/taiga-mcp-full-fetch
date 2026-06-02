# Taiga MCP Server

**Версия:** 1.1.0  
**Язык:** Python 3.11+  
**Транспорты:** SSE (`/sse/`), Streamable HTTP (`/mcp/`)

## Назначение

MCP-сервер для интеграции AI-ассистентов (ChatGPT, Claude, OpenCode) с таск-трекером [Taiga](https://taiga.io/). Предоставляет полный набор CRUD-операций: проекты, эпики, user stories, задачи, issues.

## Архитектура

```
AI-ассистент → MCP (SSE/HTTP) → Taiga MCP Server → Taiga REST API
```

**Компоненты:**
- **FastMCP** — регистрация и исполнение MCP-инструментов
- **Starlette** — SSE и Streamable HTTP транспорты
- **Action Proxy** — REST API (`/actions/*`) для HTTP-интеграций
- **Taiga Client** — асинхронный wrapper вокруг Taiga REST API (httpx)

## Быстрый старт

### Требования

- Python 3.11+ или Docker
- Аккаунт в Taiga (self-hosted или taiga.io)

### Установка

```bash
git clone https://github.com/kononeer/taiga-mcp-full-fetch.git
cd taiga-mcp-full-fetch

# Вариант 1: Docker (рекомендуется)
docker build -t taiga-mcp:latest .
docker run -d --name taiga-mcp --env-file .env -p 8010:8000 taiga-mcp:latest

# Вариант 2: Локально
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8010
```

### Конфигурация

Скопируйте `.env.example` → `.env` и заполните:

```env
# Обязательные
TAIGA_BASE_URL=https://api.taiga.io          # или ваш self-hosted URL
TAIGA_USERNAME=your-username
TAIGA_PASSWORD=your-password

# Опциональные
TAIGA_PROJECT_ID=123                         # проект по умолчанию
TAIGA_PROJECT_SLUG=your-project              # slug по умолчанию
ACTION_PROXY_API_KEY=random-key-32bytes      # ключ для REST API
DESTRUCTIVE_ENABLED=false                    # разрешить жёсткое удаление
```

### Проверка

```bash
curl http://localhost:8010/healthz    # → ok
curl http://localhost:8010/           # → Taiga MCP up
```

## Структура документации

| Файл | Содержание |
|------|-----------|
| [docs/API.md](docs/API.md) | MCP-инструменты и REST API Action Proxy |
| [docs/GUIDE.md](docs/GUIDE.md) | Примеры использования, деплой, интеграция с клиентами |

## Основные возможности

- **Полный CRUD** — создание, чтение, обновление, удаление сущностей Taiga
- **Автопагинация** — list-инструменты без параметра `page` возвращают все элементы
- **Два транспорта** — SSE и Streamable HTTP для разных MCP-клиентов
- **Action Proxy** — REST API с аутентификацией по API-ключу
- **Безопасные операции** — `append_description`, `add_tags`, `archive_or_close`
- **Оптимистичная блокировка** — проверка версий при обновлении

## Поддерживаемые сущности

| Сущность | Операции |
|----------|----------|
| Projects | list, get |
| Epics | list, get, create, update, delete, add_user_story |
| User Stories | list, get, create, update, delete, archive_or_close |
| Tasks | list, get, create, update, delete, archive_or_close |
| Issues | list, get, create, update, delete |
| Users | list |
| Milestones | list |

## Переменные окружения

### Обязательные

| Переменная | Описание |
|------------|----------|
| `TAIGA_BASE_URL` | Базовый URL Taiga API |
| `TAIGA_USERNAME` | Имя пользователя |
| `TAIGA_PASSWORD` | Пароль |

### Опциональные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TAIGA_PROJECT_ID` | ID проекта по умолчанию | — |
| `TAIGA_PROJECT_SLUG` | Slug проекта по умолчанию | — |
| `ACTION_PROXY_API_KEY` | API-ключ для Action Proxy | — |
| `DESTRUCTIVE_ENABLED` | Разрешить жёсткое удаление | `false` |

## Troubleshooting

### Результат содержит только 1 элемент

MCP SDK разбивает Python-списки на отдельные `TextContent`. В этом форке исправлено — все list-инструменты возвращают `json.dumps()` вместо raw-списка. Если проблема сохраняется:

1. Проверьте, что используется форк `kononeer/taiga-mcp-full-fetch`
2. Пересоберите образ: `docker build -t taiga-mcp:latest . && docker restart taiga-mcp`
3. Перезапустите MCP-клиент (VS Code/OpenCode)

### Конфликт версий (409)

```python
story = json.loads(taiga_stories_get(user_story_id=123))
taiga_stories_update(user_story_id=123, status="Done", version=story["version"])
```

### Ошибка аутентификации

```bash
docker logs taiga-mcp --tail 20
docker exec taiga-mcp curl -s http://localhost:8000/healthz
```

## Лицензия

Не указана.
