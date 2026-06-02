# Taiga MCP Server

**Версия:** 1.1.0  
**Репозиторий:** [OFFSET3/taiga-mcp](https://github.com/OFFSET3/taiga-mcp)  
**Лицензия:** Не указана  
**Язык:** Python 3.11+

## Назначение

Taiga MCP Server — это [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) сервер, который служит мостом между AI-ассистентами (ChatGPT, Claude и др.) и таск-трекером [Taiga](https://taiga.io/). Сервер предоставляет полный набор CRUD-операций для управления проектами, эпиками, пользовательскими историями, задачами и issues в Taiga через MCP-инструменты и REST API.

## Ключевые возможности

- **Полный CRUD** — создание, чтение, обновление и удаление сущностей Taiga
- **Два транспорта** — Server-Sent Events (SSE) и Streamable HTTP для MCP-клиентов
- **Action Proxy** — REST API для HTTP-интеграций с аутентификацией по API-ключу
- **Безопасные операции** — поддержка append-only обновлений и мягкого удаления (архивация)
- **Оптимистичная блокировка** — проверка версий при обновлении для предотвращения конфликтов
- **Идемпотентность** — кеширование для предотвращения дублирования операций
- **Контейнеризация** — готовый Docker-образ для деплоя на Azure Container Apps

## Быстрый старт

### Требования

- Python 3.11+
- Docker (опционально, для контейнерного деплоя)
- Azure CLI (опционально, для деплоя на Azure)

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/OFFSET3/taiga-mcp.git
cd taiga-mcp

# Создание виртуального окружения
python -m venv .chat-venv
source .chat-venv/bin/activate  # Linux/Mac
# или .\.chat-venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Конфигурация

```bash
# Копирование шаблона конфигурации
cp .env.example .env
```

Заполните `.env` файл:

```env
TAIGA_BASE_URL=https://taiga.example.com
TAIGA_USERNAME=service-account
TAIGA_PASSWORD=your-password
TAIGA_PROJECT_ID=123
TAIGA_PROJECT_SLUG=your-project
ACTION_PROXY_API_KEY=your-random-api-key
MCP_URL=https://your-domain.example/mcp
TAIGA_PROXY_BASE_URL=https://your-domain.example
```

### Запуск

```bash
# Локальный запуск
uvicorn app:app --host 127.0.0.1 --port 8010

# Проверка работоспособности
curl http://127.0.0.1:8010/healthz
```

## Структура документации

- [ARCHITECTURE.md](ARCHITECTURE.md) — Архитектура и компоненты системы
- [MCP_TOOLS.md](MCP_TOOLS.md) — Описание MCP-инструментов
- [ACTION_PROXY.md](ACTION_PROXY.md) — REST API Action Proxy
- [CONFIGURATION.md](CONFIGURATION.md) — Конфигурация и переменные окружения
- [DEPLOYMENT.md](DEPLOYMENT.md) — Инструкции по деплою
- [EXAMPLES.md](EXAMPLES.md) — Типовые сценарии использования
- [CLIENTS.md](CLIENTS.md) — Интеграция с MCP-клиентами

## Поддерживаемые сущности Taiga

| Сущность | Операции |
|----------|----------|
| **Projects** | list, get |
| **Epics** | list, get, create, update, delete, add_user_story |
| **User Stories** | list, get, create, update, delete, archive_or_close |
| **Tasks** | list, get, create, update, delete, archive_or_close |
| **Issues** | list, get, create, update, delete |
| **Users** | list |
| **Milestones** | list |

## Транспорты MCP

### Server-Sent Events (SSE)

- **Endpoint:** `/sse/`
- **Требования:** `Accept: text/event-stream`
- **Особенности:** В первом событии возвращает endpoint для POST-запросов

### Streamable HTTP

- **Endpoint:** `/mcp/`
- **Требования:** `Accept: application/json, text/event-stream`
- **Особенности:** Поддерживает длительные сессии для ChatGPT

## Action Proxy

REST API для HTTP-интеграций, защищённый API-ключом:

- **Base URL:** `/actions/`
- **Аутентификация:** `X-Api-Key` header
- **Формат:** JSON request/response

Подробнее в [ACTION_PROXY.md](ACTION_PROXY.md).

## Зависимости

```
mcp>=1.0
starlette>=0.37
uvicorn>=0.30
httpx>=0.27
python-dotenv>=1.0.0
```

## Тестирование

```bash
# Установка зависимостей для тестирования
pip install pytest

# Запуск тестов
pytest

# Smoke-тест MCP
python streamable_client.py $MCP_URL --message "ping"

# Проверка SSE
curl -sN -H "Accept: text/event-stream" $TAIGA_PROXY_BASE_URL/sse/
```

## Авторы

- [OFFSET3](https://github.com/OFFSET3) — организация

## Связанные проекты

- [taiga-family/taiga-ui-mcp](https://github.com/taiga-family/taiga-ui-mcp) — MCP-сервер для документации Taiga UI (Angular компоненты)
- [Taiga](https://taiga.io/) — Open Source таск-трекер

## История изменений

### v1.1.0 (Декабрь 2024)

- **GET endpoints:** `epics.get`, `stories.get`, `tasks.get`
- **DELETE endpoints:** `epics.delete`, `stories.delete`, `tasks.delete`
- **Append-only updates:** `append_description` и `add_tags`
- **Soft-delete:** `archive_or_close` helpers
- **Pagination defaults:** `page_size=50`
- **Field control:** `include_details` flag

### v1.2.0 (Апрель 2026)

- **Rename tool names:** с dot-notation на underscore для совместимости с Claude
- **Middleware:** `_NormalizeToolNames` для обратной совместимости
- **Fix routes:** корректная обработка `/mcp` и `/sse` без trailing slash

## Известные ограничения

1. **Деструктивные операции** — удаление сущностей требует явного включения через `DESTRUCTIVE_ENABLED`
2. **Версионирование** — обновление требует указания версии или использования оптимистичной блокировки
3. **Пагинация** — максимальный `page_size` ограничен 100 элементами
4. **Таймауты** — HTTP-запросы к Taiga имеют таймаут 30 секунд
5. **Аутентификация** — используется Basic Auth через username/password (не OAuth)

## Troubleshooting

### `Not Acceptable: Client must accept text/event-stream`

Убедитесь, что клиент отправляет заголовок `Accept: application/json, text/event-stream` при обращении к `/mcp/`.

### `Session terminated`

Обычно указывает на редирект. Убедитесь, что запрос идёт на `/mcp/` (с trailing slash) и прокси не перезаписывают заголовки.

### Azure CLI `WinError 5`

Установите переменные окружения:
```powershell
$env:AZURE_EXTENSION_DIR = Join-Path $HOME '.az-extensions'
$env:AZURE_CONFIG_DIR = Join-Path $HOME '.az-cli'
```

### Конфликты при обновлении (409)

При получении ошибки конфликта проверьте актуальную версию сущности и повторите запрос с обновлённой версией.
