# Руководство

## Примеры использования

### Получить stories в статусе "In progress"

```python
import json

raw = taiga_stories_list(project_id=123)
stories = json.loads(raw)

in_progress = [
    s for s in stories
    if s.get("status_extra_info", {}).get("name") == "In progress"
]

for s in in_progress:
    print(f"#{s['ref']} — {s['subject']}")
```

### Создать спринт

```python
# 1. Создать stories
story = json.loads(taiga_stories_create(
    project_id=123,
    subject="As a user, I want to login",
    description="## Acceptance Criteria\n1. ...",
    status="New",
    tags=["auth"]
))

# 2. Создать задачи
task = json.loads(taiga_tasks_create(
    user_story_id=story["id"],
    subject="Implement OAuth2",
    status="In progress",
    assigned_to=101,
    due_date="2024-06-15"
))

# 3. Привязать к эпику
taiga_epics_add_user_story(epic_id=456, user_story_id=story["id"])
```

### Обработка баг-репорта

```python
# Создать issue
issue = json.loads(taiga_issues_create(
    project_id=123,
    subject="Login form 500 error on Safari",
    description="## Steps\n1. Open Safari...",
    priority=2,
    severity=3,
    tags=["bug", "safari"]
))

# Назначить и обновить
taiga_issues_update(issue_id=issue["id"], assigned_to=102, status="In progress")

# Добавить комментарий
taiga_issues_update(
    issue_id=issue["id"],
    append_description="\n\n## Update\nFound the issue...",
    add_tags=["in-progress"]
)

# Закрыть
taiga_issues_update(issue_id=issue["id"], status="Done")
```

### Архивация завершённых задач

```python
result = json.loads(taiga_tasks_list(project_id=123, status="Done"))
for task in result["tasks"]:
    taiga_tasks_archive_or_close(
        task_id=task["id"],
        add_archive_tag=True
    )
```

### CI/CD интеграция

```yaml
# GitHub Actions — создать задачу при падении тестов
- name: Create Taiga task on failure
  if: failure()
  run: |
    curl -X POST -H "X-Api-Key: ${{ secrets.TAIGA_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{"project_id":123,"subject":"Tests failed","tags":["ci-cd"]}' \
      "http://localhost:8010/actions/create_task"
```

## Деплой

### Docker

```bash
docker build -t taiga-mcp:latest .
docker run -d --name taiga-mcp \
  --env-file .env -p 8010:8000 \
  --restart unless-stopped \
  taiga-mcp:latest
```

### Docker Compose

```yaml
services:
  taiga-mcp:
    image: taiga-mcp:latest
    ports: ["8010:8010"]
    env_file: [".env"]
    restart: unless-stopped
```

### Azure Container Apps

```bash
az containerapp create \
  --name taiga-mcp \
  --resource-group $RG \
  --image taiga-mcp:latest \
  --target-port 8010 \
  --ingress external

# Секреты
az containerapp secret set \
  --name taiga-mcp \
  --secrets taiga-password="...",action-proxy-api-key="..."
```

## Интеграция с клиентами

### OpenCode / VS Code

Добавить в `opencode.json`:

```json
{
  "mcp": {
    "taiga": {
      "type": "remote",
      "url": "http://localhost:8010/sse/",
      "enabled": true
    }
  }
}
```

Перезапустить VS Code. Агент получит доступ к инструментам Taiga.

### Claude Desktop

```json
{
  "mcpServers": {
    "taiga": {
      "command": "python",
      "args": ["/path/to/streamable_client.py", "http://localhost:8010/mcp"]
    }
  }
}
```

### ChatGPT (Custom GPT)

1. GPT Builder → Configure → Actions → Model Context Protocol
2. URL: `https://your-domain.com/mcp/`

### Прямой Python

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8010/sse/") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("taiga_projects_list", {})
        projects = json.loads(result.content[0].text)
```
