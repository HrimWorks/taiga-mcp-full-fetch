# API Reference

## MCP Инструменты

Все инструменты доступны через транспорты SSE (`/sse/`) и Streamable HTTP (`/mcp/`).

**Важно:** list-инструменты возвращают JSON-строку (`str`), которую нужно парсить через `json.loads()`.

### Чтение

#### `taiga_projects_list(search?)`

Список проектов. Возвращает JSON-массив.

```python
raw = taiga_projects_list(search="backend")
projects = json.loads(raw)  # list[dict]
```

#### `taiga_projects_get(project_id? | slug?)`

Получение проекта. Один из параметров обязателен.

```python
project = json.loads(taiga_projects_get(slug="my-project"))
```

#### `taiga_epics_list(project_id, include_details?, page?, page_size?)`

Список эпиков. Без `page` — возвращает все.

```python
epics = json.loads(taiga_epics_list(project_id=123))
```

#### `taiga_epics_get(epic_id)`

Получение эпика по ID.

#### `taiga_stories_list(project_id?, search?, epic_id?, tags?, page?, page_size?)`

Список user stories. **Без `page` — автопагинация, все stories.**

```python
stories = json.loads(taiga_stories_list(project_id=123))
# Фильтрация по статусу на клиенте:
in_progress = [s for s in stories if s.get("status_extra_info", {}).get("name") == "In progress"]
```

#### `taiga_stories_get(user_story_id)`

Получение story по ID.

#### `taiga_tasks_list(project_id?, user_story_id?, assigned_to?, search?, page?, page_size?)`

Список задач. Возвращает `{"tasks": [...], "pagination": {...}}`.

```python
result = json.loads(taiga_tasks_list(project_id=123))
tasks = result["tasks"]
```

#### `taiga_tasks_get(task_id)`

Получение задачи по ID.

#### `taiga_issues_get(issue_id)`

Получение issue по ID.

#### `taiga_users_list(project_id?, search?)`

Список пользователей.

```python
users = json.loads(taiga_users_list(project_id=123, search="john"))
```

#### `taiga_milestones_list(project_id?, search?)`

Список вех/спринтов.

### Создание

#### `taiga_stories_create(project_id, subject, description?, status?, tags?, assigned_to?)`

```python
story = json.loads(taiga_stories_create(
    project_id=123,
    subject="Новая функция",
    description="## Цель\n...",
    status="New",
    tags=["backend"]
))
```

#### `taiga_tasks_create(user_story_id, subject, description?, assigned_to?, status?, tags?, due_date?, idempotency_key?)`

```python
task = json.loads(taiga_tasks_create(
    user_story_id=456,
    subject="Реализовать endpoint",
    due_date="2024-06-15",
    idempotency_key="task-001"
))
```

#### `taiga_epics_add_user_story(epic_id, user_story_id)`

Привязка story к эпику.

#### `taiga_issues_create(project_id?, subject, description?, status?, priority?, severity?, issue_type?, assigned_to?, tags?)`

### Обновление

#### `taiga_stories_update(user_story_id, ...)`

Параметры: `subject`, `description`, `append_description`, `status`, `tags`, `add_tags`, `assigned_to`, `epic_id`, `milestone_id`, `custom_attributes`, `version`.

```python
# Добавить к описанию
taiga_stories_update(
    user_story_id=789,
    append_description="\n\n## Update\nНовая информация",
    add_tags=["urgent"]
)

# Сменить статус с optimistic locking
story = json.loads(taiga_stories_get(user_story_id=789))
taiga_stories_update(user_story_id=789, status="Done", version=story["version"])
```

#### `taiga_tasks_update(task_id, ...)`

Аналогично stories: `subject`, `description`, `append_description`, `assigned_to`, `status`, `tags`, `add_tags`, `due_date`, `version`.

#### `taiga_issues_update(issue_id, ...)`

### Удаление

#### `taiga_stories_archive_or_close(user_story_id, closed_status?, add_archive_tag?)`

Безопасное закрытие (рекомендуется).

```python
taiga_stories_archive_or_close(user_story_id=789, closed_status="Closed")
```

#### `taiga_tasks_archive_or_close(task_id, ...)`

#### `taiga_stories_delete(user_story_id)` / `taiga_tasks_delete(task_id)` / `taiga_epics_delete(epic_id)` / `taiga_issues_delete(issue_id)`

⚠️ Требует `DESTRUCTIVE_ENABLED=true`.

## Action Proxy (REST API)

REST API поверх MCP-инструментов. Защищён API-ключом.

**Base URL:** `http://localhost:8010/actions/`  
**Аутентификация:** `X-Api-Key: <ACTION_PROXY_API_KEY>`

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/actions/diagnostics` | Диагностика |
| GET | `/actions/list_projects` | Список проектов |
| GET | `/actions/get_project` | Проект по ID |
| GET | `/actions/get_project_by_slug` | Проект по slug |
| GET | `/actions/list_epics` | Список эпиков |
| GET | `/actions/get_epic` | Эпик по ID |
| GET | `/actions/list_stories` | Список stories |
| GET | `/actions/get_story` | Story по ID |
| GET | `/actions/get_task` | Задача по ID |
| GET | `/actions/statuses` | Статусы проекта |
| POST | `/actions/create_story` | Создание story |
| POST | `/actions/update_story` | Обновление story |
| POST | `/actions/delete_story` | Удаление story |
| POST | `/actions/add_story_to_epic` | Привязка к эпику |
| POST | `/actions/create_epic` | Создание эпика |
| POST | `/actions/update_epic` | Обновление эпика |
| POST | `/actions/delete_epic` | Удаление эпика |
| POST | `/actions/create_task` | Создание задачи |
| POST | `/actions/update_task` | Обновление задачи |
| POST | `/actions/delete_task` | Удаление задачи |
| POST | `/actions/create_issue` | Создание issue |
| POST | `/actions/update_issue` | Обновление issue |
| POST | `/actions/delete_issue` | Удаление issue |

### Примеры

```bash
# Список stories
curl -H "X-Api-Key: $API_KEY" \
  "http://localhost:8010/actions/list_stories?project_id=123"

# Создание story
curl -X POST -H "X-Api-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"project_id":123,"subject":"Новая story"}' \
  "http://localhost:8010/actions/create_story"

# Обновление статуса
curl -X POST -H "X-Api-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"story_id":789,"status":"Done"}' \
  "http://localhost:8010/actions/update_story"
```

### Хелпер-скрипты

```bash
# Python client
python scripts/actions_proxy_client.py --pretty list-projects

# PowerShell
powershell.exe -File scripts/actions-proxy.ps1 list-projects
```
