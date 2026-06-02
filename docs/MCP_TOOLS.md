# MCP Инструменты

## Обзор

Taiga MCP Server предоставляет 20+ инструментов для работы с сущностями Taiga. Все инструменты регистрируются через декоратор `@mcp.tool()` и доступны через MCP транспорты (SSE/Streamable HTTP).

## Соглашения

### Именование

- **Формат:** `taiga_<entity>_<action>` (underscore notation)
- **Пример:** `taiga_stories_list`, `taiga_tasks_create`
- **Legacy:** До v1.2.0 использовался dot notation (`taiga.stories.list`)

### Аннотации

Каждый инструмент имеет метаданные безопасности:

```python
ToolAnnotations(
    openWorldHint=True,        # Инструмент взаимодействует с внешним API
    readOnlyHint=True,         # Только чтение (для GET операций)
    idempotentHint=True,       # Повторный вызов даёт тот же результат
    destructiveHint=False,     # Не изменяет/удаляет данные
)
```

### Параметры

- **Обязательные:** Должны быть указаны при вызове
- **Опциональные:** Имеют значение по умолчанию или `None`
- **UNSET:** Специальное значение для частичного обновления (только поля, явно указанные в запросе)

### Возвращаемые значения

- **Фильтрация полей:** Только whitelisted поля возвращаются клиенту
- **Пагинация:** Для списков возвращается объект с `items` и `pagination`
- **Ошибки:** Возвращаются как JSON-RPC errors с описательным сообщением

## Инструменты чтения

### `taiga_projects_list`

**Назначение:** Список проектов, где service account является участником.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `search` | `string` | Нет | Фильтр по имени проекта (case-insensitive substring) |

**Возвращает:** `list[dict]`

```json
[
  {
    "id": 123,
    "name": "My Project",
    "slug": "my-project",
    "description": "Project description",
    "created_date": "2024-01-15T10:30:00Z",
    "modified_date": "2024-06-01T14:20:00Z"
  }
]
```

**Пример вызова:**

```json
{
  "name": "taiga_projects_list",
  "arguments": {
    "search": "backend"
  }
}
```

---

### `taiga_projects_get`

**Назначение:** Получение проекта по ID или slug.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет* | Числовой ID проекта |
| `slug` | `string` | Нет* | URL-friendly идентификатор |

*Один из параметров обязателен.

**Возвращает:** `dict` — полный объект проекта

**Пример вызова:**

```json
{
  "name": "taiga_projects_get",
  "arguments": {
    "slug": "my-project"
  }
}
```

---

### `taiga_epics_list`

**Назначение:** Список эпиков проекта.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Да | ID проекта |
| `include_details` | `bool` | Нет | Включить полные поля (default: false, minimal fields) |
| `page` | `int` | Нет | Номер страницы |
| `page_size` | `int` | Нет | Размер страницы (default: 50, max: 100) |

**Возвращает:** `list[dict]`

**Пример вызова:**

```json
{
  "name": "taiga_epics_list",
  "arguments": {
    "project_id": 123,
    "include_details": true,
    "page_size": 25
  }
}
```

---

### `taiga_epics_get`

**Назначение:** Получение эпика по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `epic_id` | `int` | Да | Числовой ID эпика |

**Возвращает:** `dict` — полный объект эпика

**Пример вызова:**

```json
{
  "name": "taiga_epics_get",
  "arguments": {
    "epic_id": 456
  }
}
```

---

### `taiga_stories_list`

**Назначение:** Список пользовательских историй проекта.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет* | ID проекта |
| `search` | `string` | Нет | Текстовый поиск по subject/description |
| `epic_id` | `int` | Нет | Фильтр по принадлежности к эпику |
| `tags` | `list[string]` | Нет | Фильтр по тегам |
| `page` | `int` | Нет | Номер страницы |
| `page_size` | `int` | Нет | Размер страницы (default: 50) |

*Если не указан, используется `TAIGA_PROJECT_ID` или `TAIGA_PROJECT_SLUG` из env.

**Возвращает:** `list[dict]`

```json
[
  {
    "id": 789,
    "ref": 42,
    "subject": "As a user, I want to login",
    "description": "## Acceptance Criteria\n...",
    "project": 123,
    "epic": 456,
    "tags": ["frontend", "auth"],
    "status": 1,
    "status_extra_info": {"name": "New", "color": "#999999"},
    "assigned_to": 101,
    "created_date": "2024-01-15T10:30:00Z",
    "modified_date": "2024-06-01T14:20:00Z"
  }
]
```

**Пример вызова:**

```json
{
  "name": "taiga_stories_list",
  "arguments": {
    "project_id": 123,
    "search": "login",
    "epic_id": 456,
    "tags": ["frontend"]
  }
}
```

---

### `taiga_stories_get`

**Назначение:** Получение пользовательской истории по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `user_story_id` | `int` | Да | Числовой ID истории |

**Возвращает:** `dict` — полный объект истории

**Пример вызова:**

```json
{
  "name": "taiga_stories_get",
  "arguments": {
    "user_story_id": 789
  }
}
```

---

### `taiga_tasks_list`

**Назначение:** Список задач с гибкой фильтрацией.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет | ID проекта |
| `user_story_id` | `int` | Нет | ID пользовательской истории |
| `assigned_to` | `int` | Нет | ID исполнителя |
| `search` | `string` | Нет | Текстовый поиск |
| `status` | `int \| string` | Нет | ID статуса или имя/slug |
| `page` | `int` | Нет | Номер страницы |
| `page_size` | `int` | Нет | Размер страницы |

**Возвращает:** `dict` с `tasks` и `pagination`

```json
{
  "tasks": [
    {
      "id": 1001,
      "ref": 15,
      "subject": "Implement OAuth2 flow",
      "project": 123,
      "user_story": 789,
      "status": 2,
      "description": "## Details\n...",
      "assigned_to": 101,
      "tags": ["backend", "oauth"],
      "due_date": "2024-06-15",
      "created_date": "2024-01-15T10:30:00Z",
      "modified_date": "2024-06-01T14:20:00Z",
      "version": 5
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 150,
    "total_pages": 3
  }
}
```

**Пример вызова:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "project_id": 123,
    "user_story_id": 789,
    "status": "In progress",
    "page_size": 25
  }
}
```

---

### `taiga_tasks_get`

**Назначение:** Получение задачи по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `task_id` | `int` | Да | Числовой ID задачи |

**Возвращает:** `dict` — полный объект задачи

**Пример вызова:**

```json
{
  "name": "taiga_tasks_get",
  "arguments": {
    "task_id": 1001
  }
}
```

---

### `taiga_issues_get`

**Назначение:** Получение issue по ID.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `issue_id` | `int` | Да | Числовой ID issue |

**Возвращает:** `dict` — полный объект issue

---

### `taiga_users_list`

**Назначение:** Список пользователей Taiga.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет | Фильтр по участникам проекта |
| `search` | `string` | Нет | Поиск по имени, username или email |

**Возвращает:** `list[dict]`

```json
[
  {
    "id": 101,
    "full_name": "John Doe",
    "username": "jdoe",
    "email": "john@example.com"
  }
]
```

**Пример вызова:**

```json
{
  "name": "taiga_users_list",
  "arguments": {
    "project_id": 123,
    "search": "john"
  }
}
```

---

### `taiga_milestones_list`

**Назначение:** Список вех/спринтов проекта.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет* | ID проекта |
| `search` | `string` | Нет | Поиск по имени или slug |

*Если не указан, используется `TAIGA_PROJECT_ID` или `TAIGA_PROJECT_SLUG`.

**Возвращает:** `list[dict]`

```json
[
  {
    "id": 2001,
    "name": "Sprint 1",
    "slug": "sprint-1",
    "estimated_start": "2024-01-01",
    "estimated_finish": "2024-01-14",
    "closed": false,
    "project": 123
  }
]
```

**Пример вызова:**

```json
{
  "name": "taiga_milestones_list",
  "arguments": {
    "project_id": 123,
    "search": "sprint"
  }
}
```

---

## Инструменты создания

### `taiga_stories_create`

**Назначение:** Создание пользовательской истории.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Да | ID проекта |
| `subject` | `string` | Да | Заголовок истории |
| `description` | `string` | Нет | Описание (поддерживает Markdown) |
| `status` | `int \| string` | Нет | ID статуса или имя/slug |
| `tags` | `list[string]` | Нет | Теги |
| `assigned_to` | `int` | Нет | ID исполнителя |

**Возвращает:** `dict` — созданная история

**Пример вызова:**

```json
{
  "name": "taiga_stories_create",
  "arguments": {
    "project_id": 123,
    "subject": "As a user, I want to reset my password",
    "description": "## Acceptance Criteria\n1. User can request password reset\n2. Email is sent with reset link",
    "status": "New",
    "tags": ["backend", "auth"],
    "assigned_to": 101
  }
}
```

---

### `taiga_epics_add_user_story`

**Назначение:** Привязка пользовательской истории к эпику.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `epic_id` | `int` | Да | ID эпика |
| `user_story_id` | `int` | Да | ID истории |

**Возвращает:** `dict \| None` — результат привязки

**Пример вызова:**

```json
{
  "name": "taiga_epics_add_user_story",
  "arguments": {
    "epic_id": 456,
    "user_story_id": 789
  }
}
```

---

### `taiga_tasks_create`

**Назначение:** Создание задачи для пользовательской истории.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `user_story_id` | `int` | Да | ID истории |
| `subject` | `string` | Да | Заголовок задачи |
| `description` | `string` | Нет | Описание |
| `assigned_to` | `int` | Нет | ID исполнителя |
| `status` | `int \| string` | Нет | ID статуса или имя/slug |
| `tags` | `list[string]` | Нет | Теги |
| `due_date` | `string` | Нет | Срок выполнения (YYYY-MM-DD) |
| `idempotency_key` | `string` | Нет | Ключ для предотвращения дублей |

**Возвращает:** `dict` — созданная задача

**Пример вызова:**

```json
{
  "name": "taiga_tasks_create",
  "arguments": {
    "user_story_id": 789,
    "subject": "Implement JWT token generation",
    "description": "## Implementation Details\n...",
    "status": "In progress",
    "assigned_to": 101,
    "due_date": "2024-06-15",
    "idempotency_key": "jwt-task-001"
  }
}
```

---

### `taiga_issues_create`

**Назначение:** Создание issue.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `project_id` | `int` | Нет* | ID проекта |
| `subject` | `string` | Да | Заголовок |
| `description` | `string` | Нет | Описание |
| `status` | `int` | Нет | ID статуса |
| `priority` | `int` | Нет | Приоритет |
| `severity` | `int` | Нет | Серьёзность |
| `issue_type` | `int` | Нет | Тип issue |
| `assigned_to` | `int` | Нет | ID исполнителя |
| `tags` | `list[string]` | Нет | Теги |

*Если не указан, используется `TAIGA_PROJECT_ID`.

**Возвращает:** `dict` — созданный issue

---

## Инструменты обновления

### `taiga_stories_update`

**Назначение:** Обновление пользовательской истории.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `user_story_id` | `int` | Да | ID истории |
| `subject` | `string` | Нет | Новый заголовок |
| `description` | `string` | Нет | Новое описание (перезапись) |
| `append_description` | `string` | Нет | Добавить к существующему описанию |
| `status` | `int \| string` | Нет | Новый статус |
| `tags` | `list[string]` | Нет | Новые теги (перезапись) |
| `add_tags` | `list[string]` | Нет | Добавить теги к существующим |
| `assigned_to` | `int` | Нет | Новый исполнитель |
| `epic_id` | `int` | Нет | ID эпика |
| `milestone_id` | `int` | Нет | ID вехи/спринта |
| `custom_attributes` | `dict` | Нет | Кастомные атрибуты |
| `version` | `int` | Нет | Версия для optimistic locking |

**Ограничения:**
- Нельзя одновременно указать `description` и `append_description`
- Нельзя одновременно указать `tags` и `add_tags`
- Если `version` не указан, используется текущая версия из существующей сущности

**Возвращает:** `dict` — обновлённая история

**Пример вызова (append):**

```json
{
  "name": "taiga_stories_update",
  "arguments": {
    "user_story_id": 789,
    "append_description": "\n\n## Additional Notes\nFound edge case with OAuth2.",
    "add_tags": ["bug"],
    "status": "In progress"
  }
}
```

---

### `taiga_tasks_update`

**Назначение:** Обновление задачи.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `task_id` | `int` | Да | ID задачи |
| `subject` | `string` | Нет | Новый заголовок |
| `description` | `string` | Нет | Новое описание |
| `append_description` | `string` | Нет | Добавить к описанию |
| `assigned_to` | `int` | Нет | Новый исполнитель |
| `status` | `int \| string` | Нет | Новый статус |
| `tags` | `list[string]` | Нет | Новые теги |
| `add_tags` | `list[string]` | Нет | Добавить теги |
| `due_date` | `string` | Нет | Новый срок |
| `version` | `int` | Нет | Версия для optimistic locking |

**Возвращает:** `dict` — обновлённая задача

---

### `taiga_issues_update`

**Назначение:** Обновление issue.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `issue_id` | `int` | Да | ID issue |
| `subject` | `string` | Нет | Новый заголовок |
| `description` | `string` | Нет | Новое описание |
| `append_description` | `string` | Нет | Добавить к описанию |
| `status` | `int` | Нет | Новый статус |
| `priority` | `int` | Нет | Приоритет |
| `severity` | `int` | Нет | Серьёзность |
| `issue_type` | `int` | Нет | Тип |
| `assigned_to` | `int` | Нет | Исполнитель |
| `tags` | `list[string]` | Нет | Теги |
| `add_tags` | `list[string]` | Нет | Добавить теги |
| `version` | `int` | Нет | Версия |

**Возвращает:** `dict` — обновлённый issue

---

## Инструменты удаления

### Жёсткое удаление (DESTRUCTIVE)

⚠️ Требует `DESTRUCTIVE_ENABLED=true` в переменных окружения.

#### `taiga_stories_delete`

**Назначение:** Полное удаление пользовательской истории.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `user_story_id` | `int` | Да | ID истории |

**Возвращает:** `dict` — подтверждение удаления

```json
{"id": 789, "deleted": true}
```

---

#### `taiga_tasks_delete`

**Назначение:** Полное удаление задачи.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `task_id` | `int` | Да | ID задачи |

**Возвращает:** `dict` — подтверждение удаления

---

#### `taiga_epics_delete`

**Назначение:** Полное удаление эпика.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `epic_id` | `int` | Да | ID эпика |

**Возвращает:** `dict` — подтверждение удаления

---

#### `taiga_issues_delete`

**Назначение:** Полное удаление issue.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `issue_id` | `int` | Да | ID issue |

**Возвращает:** `dict` — подтверждение удаления

---

### Мягкое удаление (archive_or_close)

Безопасная альтернатива жёсткому удалению — изменение статуса на "closed" и добавление тега архивации.

#### `taiga_stories_archive_or_close`

**Назначение:** Архивация пользовательской истории.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `user_story_id` | `int` | Да | ID истории |
| `closed_status` | `int \| string` | Нет | Статус для закрытия (default: первый closed статус) |
| `add_archive_tag` | `bool` | Нет | Добавить тег `archived-by-mcp` (default: true) |

**Возвращает:** `dict` — обновлённая история

**Пример вызова:**

```json
{
  "name": "taiga_stories_archive_or_close",
  "arguments": {
    "user_story_id": 789,
    "closed_status": "Closed",
    "add_archive_tag": true
  }
}
```

---

#### `taiga_tasks_archive_or_close`

**Назначение:** Архивация задачи.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `task_id` | `int` | Да | ID задачи |
| `closed_status` | `int \| string` | Нет | Статус для закрытия |
| `add_archive_tag` | `bool` | Нет | Добавить тег `archived-by-mcp` (default: true) |

**Возвращает:** `dict` — обновлённая задача

---

## Вспомогательные инструменты

### `echo`

**Назначение:** Диагностический инструмент для проверки соединения.

**Параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|--------------|----------|
| `message` | `string` | Да | Сообщение для возврата |

**Возвращает:** `dict` — `{ "message": "..." }`

**Пример вызова:**

```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, Taiga MCP!"
  }
}
```

---

## Резолвинг статусов

При указании статуса строкой (name или slug) сервер автоматически резолвит его в числовой ID:

```python
async def _resolve_user_story_status_id(client, project_id: int, status: int | str | None) -> int | None:
    if status is None:
        return None
    if isinstance(status, int):
        return status

    # Получаем все статусы проекта
    statuses = await client.list_user_story_statuses(project_id)
    for entry in statuses:
        if entry.get("name") == status or entry.get("slug") == status:
            return entry.get("id")
    raise TaigaAPIError(f"Status '{status}' not found for project {project_id}")
```

**Пример:**
- `"New"` → `1`
- `"in-progress"` → `2`
- `2` → `2` (уже число, возвращается как есть)

---

## Фильтрация полей

Все инструменты чтения применяют `_slice()` для фильтрации полей:

```python
def _slice(data: dict[str, Any], keep: tuple[str, ...]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k in keep}
```

**Пример для stories:**

```python
keep = (
    "id", "ref", "subject", "description", "project",
    "epic", "epics", "tags", "status", "status_extra_info",
    "assigned_to", "created_date", "modified_date",
)
```

Это уменьшает размер ответа и скрывает внутренние поля Taiga API.

---

## Обработка ошибок

### Типичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ValueError: subject is required` | Не указан обязательный параметр | Укажите `subject` |
| `ValueError: Cannot set both 'description' and 'append_description'` | Конфликт параметров | Используйте только один |
| `ValueError: At least one field must be provided` | Нет полей для обновления | Укажите хотя бы одно поле |
| `TaigaAPIError: Status '...' not found` | Неверное имя статуса | Проверьте доступные статусы |
| `ValueError: Conflict updating ...: latest version is N` | Конфликт optimistic locking | Получите актуальную версию и повторите |
| `TaigaAPIError: Environment variable ... must be configured` | Отсутствует env переменная | Настройте `.env` |

### Пример обработки конфликта

```python
# 1. Получаем актуальную версию
story = await taiga_stories_get(user_story_id=789)
current_version = story["version"]

# 2. Повторяем обновление с актуальной версией
await taiga_stories_update(
    user_story_id=789,
    status="Done",
    version=current_version
)
```
