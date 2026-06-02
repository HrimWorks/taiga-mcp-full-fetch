# Action Proxy REST API

## Обзор

Action Proxy — это REST API поверх MCP-инструментов, предоставляющий HTTP-интерфейс для интеграции с внешними системами. Он защищён API-ключом и возвращает JSON-ответы.

**Назначение:**
- Интеграция с системами, не поддерживающими MCP
- Webhook-обработчики
- Скрипты автоматизации
- Прямой доступ через curl/HTTP-клиенты

## Аутентификация

Все запросы к Action Proxy требуют заголовок `X-Api-Key`:

```http
X-Api-Key: your-secret-api-key
```

**Поведение при ошибках аутентификации:**

| Сценарий | HTTP Status | Ответ |
|----------|-------------|-------|
| Отсутствует заголовок | 401 | `{"error": "Missing X-Api-Key header"}` |
| Неверный ключ | 401 | `{"error": "Invalid API key"}` |
| Не настроен `ACTION_PROXY_API_KEY` | 503 | `{"error": "Action Proxy not configured"}` |

## Базовый URL

```
https://your-domain.example/actions/
```

## Эндпоинты

### Диагностика

#### `GET /actions/diagnostics`

**Назначение:** Проверка работоспособности и конфигурации.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `slug` | `string` | Нет | Project slug для проверки видимости |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/diagnostics?slug=my-project"
```

**Пример ответа:**

```json
{
  "status": "ok",
  "taiga_connection": true,
  "projects_visible": 5,
  "project_match": true
}
```

---

### Проекты

#### `GET /actions/list_projects`

**Назначение:** Список проектов с фильтрацией.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `search` | `string` | Нет | Фильтр по имени (case-insensitive) |
| `member` | `int` | Нет | Фильтр по ID участника (default: service account) |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/list_projects?search=backend"
```

**Пример ответа:**

```json
{
  "projects": [
    {
      "id": 123,
      "name": "Backend API",
      "slug": "backend-api",
      "description": "REST API development"
    }
  ]
}
```

---

#### `GET /actions/get_project`

**Назначение:** Получение проекта по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Да | Числовой ID проекта |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/get_project?project_id=123"
```

**Пример ответа:**

```json
{
  "project": {
    "id": 123,
    "name": "Backend API",
    "slug": "backend-api",
    "description": "REST API development",
    "created_date": "2024-01-15T10:30:00Z",
    "modified_date": "2024-06-01T14:20:00Z",
    "members": [...],
    "roles": [...]
  }
}
```

---

#### `GET /actions/get_project_by_slug`

**Назначение:** Получение проекта по slug.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `slug` | `string` | Да | URL-friendly идентификатор |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/get_project_by_slug?slug=backend-api"
```

---

### Эпики

#### `GET /actions/list_epics`

**Назначение:** Список эпиков.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет* | ID проекта (repeatable) |
| `slug` | `string` | Нет | Project slug для резолва project_id |

*Если не указан, используется `TAIGA_PROJECT_ID`.

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/list_epics?project_id=123"
```

**Пример ответа:**

```json
{
  "epics": [
    {
      "id": 456,
      "ref": 10,
      "subject": "Authentication System",
      "project_id": 123,
      "status": 1,
      "color": "#999999",
      "tags": ["backend", "security"]
    }
  ]
}
```

---

#### `GET /actions/get_epic`

**Назначение:** Получение эпика по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `epic_id` | `int` | Да | Числовой ID эпика |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/get_epic?epic_id=456"
```

---

### Истории

#### `GET /actions/list_stories`

**Назначение:** Список пользовательских историй.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Да | ID проекта |
| `epic_id` | `int` | Нет | Фильтр по эпику |
| `search` | `string` | Нет | Текстовый поиск |
| `tag` | `string` | Нет | Фильтр по тегу (repeatable) |
| `page` | `int` | Нет | Номер страницы |
| `page_size` | `int` | Нет | Размер страницы |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/list_stories?project_id=123&epic_id=456&search=login&tag=frontend"
```

**Пример ответа:**

```json
{
  "stories": [
    {
      "id": 789,
      "ref": 42,
      "subject": "As a user, I want to login",
      "project_id": 123,
      "epic_id": 456,
      "status": "New",
      "tags": ["frontend", "auth"]
    }
  ]
}
```

---

#### `GET /actions/get_story`

**Назначение:** Получение истории по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `story_id` | `int` | Да | Числовой ID истории |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/get_story?story_id=789"
```

---

### Задачи

#### `GET /actions/get_task`

**Назначение:** Получение задачи по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `task_id` | `int` | Да | Числовой ID задачи |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/get_task?task_id=1001"
```

---

### Статусы

#### `GET /actions/statuses`

**Назначение:** Список статусов проекта.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Да | ID проекта |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/statuses?project_id=123"
```

**Пример ответа:**

```json
{
  "statuses": [
    {
      "id": 1,
      "name": "New",
      "slug": "new",
      "color": "#999999",
      "is_closed": false
    },
    {
      "id": 2,
      "name": "In progress",
      "slug": "in-progress",
      "color": "#ff9900",
      "is_closed": false
    },
    {
      "id": 3,
      "name": "Done",
      "slug": "done",
      "color": "#669900",
      "is_closed": true
    }
  ]
}
```

---

### Создание историй

#### `POST /actions/create_story`

**Назначение:** Создание пользовательской истории.

**Тело запроса:**

```json
{
  "project_id": 123,
  "subject": "As a user, I want to reset my password",
  "description": "## Acceptance Criteria\n1. User can request password reset",
  "status": "New",
  "tags": ["backend", "auth"],
  "assigned_to": 101
}
```

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Да | ID проекта |
| `subject` | `string` | Да | Заголовок |
| `description` | `string` | Нет | Описание |
| `status` | `int \| string` | Нет | ID или имя статуса |
| `tags` | `list[string]` | Нет | Теги |
| `assigned_to` | `int` | Нет | ID исполнителя |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id":123,"subject":"New Story"}' \
  "$TAIGA_PROXY_BASE_URL/actions/create_story"
```

**Пример ответа:**

```json
{
  "story": {
    "id": 790,
    "ref": 43,
    "subject": "New Story",
    "project": 123,
    "status": 1,
    "created_date": "2024-06-02T10:00:00Z"
  }
}
```

---

### Обновление историй

#### `POST /actions/update_story`

**Назначение:** Обновление пользовательской истории.

**Тело запроса:**

```json
{
  "story_id": 789,
  "subject": "Updated subject",
  "status": "In progress",
  "tags": ["frontend", "auth", "urgent"]
}
```

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `story_id` | `int` | Да | ID истории |
| `project_id` | `int` | Нет | ID проекта |
| `subject` | `string` | Нет | Новый заголовок |
| `description` | `string` | Нет | Новое описание |
| `status` | `int \| string` | Нет | Новый статус |
| `tags` | `list[string]` | Нет | Новые теги |
| `assigned_to` | `int` | Нет | Новый исполнитель |

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"story_id":789,"status":"Done"}' \
  "$TAIGA_PROXY_BASE_URL/actions/update_story"
```

---

### Удаление историй

#### `POST /actions/delete_story`

**Назначение:** Удаление пользовательской истории.

**Тело запроса:**

```json
{
  "story_id": 789
}
```

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"story_id":789}' \
  "$TAIGA_PROXY_BASE_URL/actions/delete_story"
```

**Пример ответа:**

```json
{
  "deleted": {
    "story_id": 789
  }
}
```

---

### Привязка к эпику

#### `POST /actions/add_story_to_epic`

**Назначение:** Привязка истории к эпику.

**Тело запроса:**

```json
{
  "epic_id": 456,
  "user_story_id": 789
}
```

**Пример запроса:**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"epic_id":456,"user_story_id":789}' \
  "$TAIGA_PROXY_BASE_URL/actions/add_story_to_epic"
```

**Пример ответа:**

```json
{
  "link": {
    "epic": 456,
    "user_story": 789,
    "created_date": "2024-06-02T10:00:00Z"
  }
}
```

---

### Эпики

#### `POST /actions/create_epic`

**Тело запроса:**

```json
{
  "project_id": 123,
  "subject": "Authentication Epic",
  "description": "All auth-related stories",
  "status": 1,
  "assigned_to": 101,
  "tags": ["backend", "security"],
  "color": "#999999"
}
```

#### `POST /actions/update_epic`

**Тело запроса:**

```json
{
  "epic_id": 456,
  "subject": "Updated Epic",
  "color": "#ff9900"
}
```

#### `POST /actions/delete_epic`

**Тело запроса:**

```json
{
  "epic_id": 456
}
```

---

### Задачи

#### `POST /actions/create_task`

**Тело запроса:**

```json
{
  "project_id": 123,
  "user_story_id": 789,
  "subject": "Implement JWT",
  "description": "Generate and validate JWT tokens",
  "status": "In progress",
  "assigned_to": 101,
  "tags": ["backend"]
}
```

#### `POST /actions/update_task`

**Тело запроса:**

```json
{
  "task_id": 1001,
  "subject": "Updated task",
  "status": "Done"
}
```

#### `POST /actions/delete_task`

**Тело запроса:**

```json
{
  "task_id": 1001
}
```

---

### Issues

#### `POST /actions/create_issue`

**Тело запроса:**

```json
{
  "project_id": 123,
  "subject": "Bug in login form",
  "description": "Error message not displayed",
  "status": 1,
  "priority": 2,
  "severity": 3,
  "type": 1,
  "assigned_to": 101,
  "tags": ["bug", "frontend"]
}
```

#### `POST /actions/update_issue`

**Тело запроса:**

```json
{
  "issue_id": 2001,
  "status": "In progress",
  "priority": 1
}
```

#### `POST /actions/delete_issue`

**Тело запроса:**

```json
{
  "issue_id": 2001
}
```

---

## OpenAPI Schema

Action Proxy предоставляет OpenAPI 3.0.3 спецификацию:

```bash
curl "$TAIGA_PROXY_BASE_URL/openapi.json"
```

**Особенности:**
- Security scheme: `ApiKeyAuth` (header `X-Api-Key`)
- Все схемы запросов/ответов: `{"type": "object", "additionalProperties": true}`
- Servers: требует замены `REPLACE_WITH_YOUR_TAIGA_MCP_HOST`

---

## Хелпер-скрипты

### Python Client

```bash
# Список проектов
python scripts/actions_proxy_client.py --pretty list-projects

# Получение проекта
python scripts/actions_proxy_client.py get-project --project-id 123

# Получение по slug
python scripts/actions_proxy_client.py get-project-by-slug --slug backend-api
```

### PowerShell

```powershell
# Список проектов
powershell.exe -File scripts/actions-proxy.ps1 list-projects

# Создание истории
powershell.exe -File scripts/actions-proxy.ps1 create-story `
  -ProjectId 123 `
  -Subject "New Story" `
  -Status "New"
```

### curl

```bash
# Список проектов
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/list_projects?search=backend"

# Создание истории
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id":123,"subject":"Story"}' \
  "$TAIGA_PROXY_BASE_URL/actions/create_story"
```

---

## Обработка ошибок

### Формат ошибок

```json
{
  "error": "Описание ошибки"
}
```

### HTTP статусы

| Статус | Значение |
|--------|----------|
| 200 | Успешно |
| 400 | Невалидные параметры |
| 401 | Ошибка аутентификации (API-ключ) |
| 404 | Сущность не найдена |
| 500 | Внутренняя ошибка сервера |

### Примеры ошибок

**Невалидный статус:**

```json
{
  "error": "Status 'Invalid' not found for project 123"
}
```

**Конфликт версий:**

```json
{
  "error": "Conflict updating story 789: latest version is 5"
}
```

**Отсутствует обязательное поле:**

```json
{
  "error": "subject is required"
}
```

---

## Сравнение с MCP Tools

| Характеристика | MCP Tools | Action Proxy |
|----------------|-----------|--------------|
| **Транспорт** | SSE / Streamable HTTP | HTTP REST |
| **Формат** | JSON-RPC | JSON |
| **Аутентификация** | MCP session | X-Api-Key header |
| **Клиенты** | ChatGPT, Claude Desktop | curl, fetch, axios |
| **Batch calls** | Нет | Нет |
| **Streaming** | Да (SSE) | Нет |
| **Интеграция** | AI-ассистенты | Вебхуки, скрипты |

---

## Безопасность

### Рекомендации

1. **API-ключ:** Используйте криптографически стойкий случайный ключ (минимум 32 байта)
2. **HTTPS:** Всегда используйте HTTPS в production
3. **CORS:** Настройте CORS если Action Proxy доступен из браузера
4. **Rate limiting:** Рассмотрите добавление rate limiting на уровне reverse proxy
5. **Логирование:** Логируйте все запросы с IP и timestamp

### Ротация ключа

```bash
# Azure Container Apps
az containerapp secret set \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --secrets action-proxy-api-key="$(openssl rand -hex 32)"

az containerapp update \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --set-env-vars ACTION_PROXY_API_KEY=secretref:action-proxy-api-key
```
