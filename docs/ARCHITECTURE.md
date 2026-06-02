# Архитектура Taiga MCP Server

## Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client (ChatGPT/Claude)                │
│                     • SSE транспорт                           │
│                     • Streamable HTTP                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Taiga MCP Server (Python/Starlette)              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              FastMCP (Model Context Protocol)           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │  │
│  │  │   SSE       │  │ Streamable  │  │   MCP Tools  │  │  │
│  │  │ Transport   │  │   HTTP      │  │  Registry    │  │  │
│  │  │  (/sse/)    │  │ (/mcp/)     │  │              │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Action Proxy (REST API)                    │  │
│  │  • /actions/* endpoints                                 │  │
│  │  • X-Api-Key аутентификация                             │  │
│  │  • JSON request/response                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Taiga Client (httpx)                       │  │
│  │  • Аутентификация через Bearer token                    │  │
│  │  • Нормализация base URL                                │  │
│  │  • Обработка пагинации                                  │  │
│  │  • Управление сессиями                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Taiga REST API (/api/v1/)                      │
│  • /auth                                                    │
│  • /projects                                                │
│  • /epics                                                   │
│  • /userstories                                             │
│  • /tasks                                                   │
│  • /issues                                                  │
│  • /users                                                   │
│  • /milestones                                              │
└─────────────────────────────────────────────────────────────┘
```

## Компоненты системы

### 1. FastMCP Server (`app.py`)

Центральный компонент, реализующий Model Context Protocol:

- **Инициализация:** Создаёт экземпляр `McpServer` с метаданными и инструкциями
- **Регистрация инструментов:** Все MCP-инструменты регистрируются через декоратор `@mcp.tool()`
- **Транспорты:** Поддерживает SSE и Streamable HTTP через Starlette
- **Жизненный цикл:** Управление сессиями через `lifespan` hook

```python
# Пример регистрации инструмента
@mcp.tool(
    name="taiga_projects_list",
    annotations=ToolAnnotations(
        openWorldHint=True,
        readOnlyHint=True,
        idempotentHint=True
    ),
)
async def taiga_projects_list(search: str | None = None) -> list[dict[str, Any]]:
    """List projects where the service account is a member."""
    ...
```

### 2. Taiga Client (`taiga_client.py`)

Тонкий асинхронный wrapper вокруг Taiga REST API:

- **Аутентификация:** Получение Bearer token через `/auth` endpoint
- **Нормализация URL:** Автоматическое добавление `/api/v1` если отсутствует
- **Обработка ошибок:** Кастомные исключения `TaigaAPIError` с HTTP статусами
- **Пагинация:** Извлечение метаданных пагинации из заголовков ответа

```python
class TaigaClient:
    def __init__(self):
        base_url = _require_env("TAIGA_BASE_URL")
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={"Accept": "application/json"},
        )
```

### 3. Action Proxy (`app.py` — routes)

REST API для HTTP-интеграций:

- **Аутентификация:** Проверка `X-Api-Key` header
- **Маршрутизация:** Отдельные endpoints для каждой операции
- **Валидация:** Проверка входных параметров
- **Преобразование:** Конвертация HTTP запросов в вызовы Taiga API

### 4. Middleware

#### `_NormalizeToolNames`

ASGI middleware для обратной совместимости:

- **Назначение:** Преобразует dot-notation имена инструментов (`taiga.projects.list`) в underscore (`taiga_projects_list`)
- **Причина:** Версия v1.2.0 переименовала инструменты для совместимости с Claude
- **Работа:** Буферизует тело запроса, модифицирует JSON-RPC payload

#### Path Normalization

- **Назначение:** Обработка запросов без trailing slash
- **Проблема:** Автоматические редиректы Starlette удаляли MCP session headers
- **Решение:** Custom middleware переписывает `/mcp` → `/mcp/` до обработки роутером

## Поток данных

### MCP Tool Call

```
1. MCP Client отправляет JSON-RPC request
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "taiga_stories_list",
       "arguments": {"project_id": 123}
     }
   }

2. Transport layer (SSE/HTTP) принимает запрос

3. _NormalizeToolNames middleware проверяет имя инструмента

4. FastMCP router находит зарегистрированный handler

5. Handler вызывает TaigaClient через async context manager

6. TaigaClient:
   a. Проверяет аутентификацию (lazy auth)
   b. Выполняет HTTP запрос к Taiga API
   c. Обрабатывает ответ и ошибки

7. Handler фильтрует поля ответа (whitelist через _slice)

8. Результат возвращается клиенту в JSON-RPC response
```

### Action Proxy Call

```
1. HTTP Client отправляет запрос
   POST /actions/create_story
   X-Api-Key: secret-key
   {"project_id": 123, "subject": "New Story"}

2. Action Proxy middleware проверяет API-ключ

3. Route handler валидирует параметры

4. Handler вызывает соответствующий MCP tool или TaigaClient напрямую

5. Результат возвращается как JSON response
```

## Управление состоянием

### Глобальное состояние (`state`)

```python
class IndexState:
    sections: list[DocSection]        # Загруженные секции документации
    overview: str | None               # Обзор документации
    migrationGuide: str | None        # Руководство по миграции
    sourceUrl: str | None             # URL источника данных
    lastLoadedAt: int | None          # Timestamp последней загрузки
```

### Идемпотентность

```python
_IDEMPOTENCY_STORE: dict[str, Any] = {}

def _make_idempotency_cache_key(raw_key: str, user_story_id: int, subject: str) -> str:
    digest = hashlib.sha256(f"{user_story_id}:{subject}".encode("utf-8")).hexdigest()
    return f"{raw_key}:{digest}"
```

- **Ключ:** SHA256 хеш от `user_story_id:subject`
- **Хранение:** In-memory dictionary
- **Срок жизни:** До перезапуска сервера

### Оптимистичная блокировка

```python
# При обновлении сущности
if version is UNSET:
    # Автоматически использует текущую версию из существующей сущности
    version_value = existing.get("version")
    payload["version"] = int(version_value)

# При конфликте (409)
except TaigaAPIError as exc:
    if exc.status_code == 409:
        latest = await client.get_user_story(user_story_id)
        raise ValueError(f"Conflict: latest version is {latest.get('version')}")
```

## Обработка ошибок

### Иерархия исключений

```
RuntimeError
└── TaigaAPIError
    ├── status_code: int | None
    ├── payload: Any | None
    └── message: str
```

### Коды ошибок

| HTTP Status | Значение |
|-------------|----------|
| 400 | Невалидные параметры |
| 401 | Ошибка аутентификации в Taiga |
| 403 | Нет прав доступа |
| 404 | Сущность не найдена |
| 409 | Конфликт версий (optimistic locking) |
| 500 | Внутренняя ошибка сервера |

### Обработка в MCP Tools

```python
async with get_taiga_client() as client:
    try:
        result = await client.some_operation()
    except TaigaAPIError as exc:
        if exc.status_code == 401:
            # Проблема с аутентификацией
            raise
        elif exc.status_code == 404:
            # Сущность не найдена
            raise ValueError(f"Entity not found: {exc.message}")
        else:
            raise
```

## Жизненный цикл приложения

### Startup

1. **Загрузка конфигурации** — чтение переменных окружения
2. **Инициализация FastMCP** — создание сервера с метаданными
3. **Регистрация инструментов** — все `@mcp.tool()` декораторы
4. **Загрузка источника** — `ensureSourceLoaded()` (если настроено)
5. **Запуск транспорта** — подключение SSE/HTTP

### Runtime

1. **Приём запроса** — SSE или HTTP транспорт
2. **Middleware** — нормализация имён, путей
3. **Маршрутизация** — поиск handler'а
4. **Выполнение** — вызов Taiga API
5. **Фильтрация** — применение `_slice()` к результату
6. **Ответ** — JSON-RPC или HTTP response

### Shutdown

1. **Закрытие транспорта** — отключение клиентов
2. **Очистка сессий** — завершение TaigaClient сессий
3. **Освобождение ресурсов** — закрытие HTTP соединений

## Производительность

### Оптимизации

- **Lazy authentication** — аутентификация в Taiga выполняется только при первом запросе
- **Connection pooling** — httpx.AsyncClient reuse connections
- **Field filtering** — `_slice()` уменьшает размер ответа, передавая только нужные поля
- **Pagination defaults** — `page_size=50` предотвращает передачу больших payload'ов

### Ограничения

- **In-memory кеш** — идемпотентность теряется при перезапуске
- **Single-threaded** — Starlette async, но нет распределённого кеша
- **HTTP timeout** — 30 секунд на запрос к Taiga

## Безопасность

### Аутентификация

| Компонент | Метод | Переменная |
|-----------|-------|------------|
| Taiga API | Bearer Token | `TAIGA_USERNAME` + `TAIGA_PASSWORD` |
| Action Proxy | API Key | `ACTION_PROXY_API_KEY` |

### Авторизация

- **MCP Tools** — доступ через MCP client (обычно ChatGPT с настроенными permissions)
- **Action Proxy** — проверка `X-Api-Key` header на каждый запрос
- **Taiga permissions** — соблюдаются права доступа Taiga (service account)

### Деструктивные операции

```python
DESTRUCTIVE_ENABLED = os.getenv("DESTRUCTIVE_ENABLED", "false").lower() == "true"

# Удаление доступно только если явно включено
if DESTRUCTIVE_ENABLED:
    taiga_stories_delete = mcp.tool(
        name="taiga_stories_delete",
        annotations=ToolAnnotations(
            openWorldHint=True,
            idempotentHint=True,
            destructiveHint=True
        ),
    )(taiga_stories_delete)
```

## Мониторинг

### Health Checks

| Endpoint | Назначение |
|----------|------------|
| `GET /` | Корневая страница — "Taiga MCP up" |
| `GET /healthz` | Liveness probe для оркестраторов |

### Логирование

```python
# Уровни логирования
logInfo(f"Server running. Fetched components: {state.sections.length}")
logError('Initial source load failed', error)
logger.info("_NormalizeToolNames: rewrote '%s' -> '%s'", original, normalized)
```

### Azure Logs

```bash
az containerapp logs show \
  -g $AZURE_RESOURCE_GROUP \
  -n $AZURE_CONTAINER_APP \
  --tail 50
```
