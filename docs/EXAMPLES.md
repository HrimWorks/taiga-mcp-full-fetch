# Примеры использования

## Обзор

Этот раздел содержит типовые сценарии использования Taiga MCP Server. Каждый сценарий включает последовательность вызовов инструментов с примерами запросов и ответов.

## Сценарий 1: Создание нового спринта

### Цель

Создать новый спринт (milestone) и наполнить его пользовательскими историями.

### Шаги

#### 1.1. Получение списка проектов

**Запрос:**

```json
{
  "name": "taiga_projects_list",
  "arguments": {
    "search": "backend"
  }
}
```

**Ответ:**

```json
[
  {
    "id": 123,
    "name": "Backend API",
    "slug": "backend-api"
  }
]
```

#### 1.2. Получение доступных статусов

**Запрос (через Action Proxy):**

```bash
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/statuses?project_id=123"
```

**Ответ:**

```json
{
  "statuses": [
    {"id": 1, "name": "New", "slug": "new"},
    {"id": 2, "name": "In progress", "slug": "in-progress"},
    {"id": 3, "name": "Done", "slug": "done", "is_closed": true}
  ]
}
```

#### 1.3. Создание пользовательских историй

**Запрос:**

```json
{
  "name": "taiga_stories_create",
  "arguments": {
    "project_id": 123,
    "subject": "As a user, I want to login with OAuth2",
    "description": "## Acceptance Criteria\n1. User can click 'Login with Google'\n2. OAuth2 flow completes successfully\n3. User session is created",
    "status": "New",
    "tags": ["auth", "oauth", "sprint-1"]
  }
}
```

**Ответ:**

```json
{
  "id": 1001,
  "ref": 50,
  "subject": "As a user, I want to login with OAuth2",
  "project": 123,
  "status": 1,
  "tags": ["auth", "oauth", "sprint-1"],
  "created_date": "2024-06-15T10:00:00Z"
}
```

#### 1.4. Создание задач для истории

**Запрос:**

```json
{
  "name": "taiga_tasks_create",
  "arguments": {
    "user_story_id": 1001,
    "subject": "Implement OAuth2 callback handler",
    "description": "Handle OAuth2 callback from Google\n\n## Technical Details\n- Validate state parameter\n- Exchange code for token\n- Create user session",
    "status": "In progress",
    "assigned_to": 101,
    "due_date": "2024-06-20",
    "tags": ["backend", "auth"],
    "idempotency_key": "oauth-callback-001"
  }
}
```

**Ответ:**

```json
{
  "id": 2001,
  "ref": 15,
  "subject": "Implement OAuth2 callback handler",
  "user_story": 1001,
  "status": 2,
  "assigned_to": 101,
  "due_date": "2024-06-20",
  "tags": ["backend", "auth"]
}
```

#### 1.5. Получение списка задач истории

**Запрос:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "user_story_id": 1001
  }
}
```

**Ответ:**

```json
{
  "tasks": [
    {
      "id": 2001,
      "ref": 15,
      "subject": "Implement OAuth2 callback handler",
      "status": 2,
      "assigned_to": 101
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 1,
    "total_pages": 1
  }
}
```

---

## Сценарий 2: Ежедневный stand-up отчёт

### Цель

Получить список задач в работе и завершённые за последние 24 часа.

### Шаги

#### 2.1. Получение списка задач по статусу

**Запрос:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "project_id": 123,
    "status": "In progress",
    "page_size": 100
  }
}
```

**Ответ:**

```json
{
  "tasks": [
    {
      "id": 2001,
      "ref": 15,
      "subject": "Implement OAuth2 callback handler",
      "assigned_to": 101,
      "due_date": "2024-06-20"
    },
    {
      "id": 2002,
      "ref": 16,
      "subject": "Write JWT token validation",
      "assigned_to": 102,
      "due_date": "2024-06-18"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total": 2,
    "total_pages": 1
  }
}
```

#### 2.2. Получение информации об исполнителях

**Запрос:**

```json
{
  "name": "taiga_users_list",
  "arguments": {
    "project_id": 123
  }
}
```

**Ответ:**

```json
[
  {
    "id": 101,
    "full_name": "John Doe",
    "username": "jdoe",
    "email": "john@example.com"
  },
  {
    "id": 102,
    "full_name": "Jane Smith",
    "username": "jsmith",
    "email": "jane@example.com"
  }
]
```

#### 2.3. Получение завершённых задач

**Запрос:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "project_id": 123,
    "status": "Done",
    "page_size": 50
  }
}
```

**Ответ:**

```json
{
  "tasks": [
    {
      "id": 1999,
      "ref": 14,
      "subject": "Setup CI/CD pipeline",
      "assigned_to": 101,
      "modified_date": "2024-06-14T16:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 1,
    "total_pages": 1
  }
}
```

### Автоматизация через Action Proxy

```bash
#!/bin/bash
# daily-standup.sh

API_KEY="your-api-key"
BASE_URL="https://mcp.example.com"
PROJECT_ID=123

echo "=== Daily Stand-up Report ==="
echo "Date: $(date)"
echo ""

echo "In Progress:"
curl -s -H "X-Api-Key: $API_KEY" \
  "$BASE_URL/actions/list_tasks?project_id=$PROJECT_ID&status=In%20progress" | \
  jq '.tasks[] | "\(.ref): \(.subject) (Assigned: \(.assigned_to))"'

echo ""
echo "Done (last 24h):"
curl -s -H "X-Api-Key: $API_KEY" \
  "$BASE_URL/actions/list_tasks?project_id=$PROJECT_ID&status=Done" | \
  jq '.tasks[] | select(.modified_date | fromdateiso8601 > now - 86400) | "\(.ref): \(.subject)"'
```

---

## Сценарий 3: Обработка баг-репортов

### Цель

Создать issue для бага, назначить исполнителя и отслеживать статус.

### Шаги

#### 3.1. Создание issue

**Запрос:**

```json
{
  "name": "taiga_issues_create",
  "arguments": {
    "project_id": 123,
    "subject": "Login form shows 500 error on Safari",
    "description": "## Bug Description\nWhen user tries to login on Safari 15+, the server returns 500 error.\n\n## Steps to Reproduce\n1. Open Safari 15\n2. Go to /login\n3. Enter valid credentials\n4. Click 'Login'\n\n## Expected Behavior\nUser should be redirected to dashboard\n\n## Actual Behavior\n500 Internal Server Error\n\n## Environment\n- Safari 15.3\n- macOS 12.2",
    "priority": 2,
    "severity": 3,
    "issue_type": 1,
    "tags": ["bug", "safari", "frontend", "urgent"]
  }
}
```

**Ответ:**

```json
{
  "id": 3001,
  "ref": 25,
  "subject": "Login form shows 500 error on Safari",
  "project": 123,
  "priority": 2,
  "severity": 3,
  "issue_type": 1,
  "tags": ["bug", "safari", "frontend", "urgent"],
  "created_date": "2024-06-15T11:00:00Z"
}
```

#### 3.2. Назначение исполнителя

**Запрос:**

```json
{
  "name": "taiga_issues_update",
  "arguments": {
    "issue_id": 3001,
    "assigned_to": 102,
    "status": "In progress",
    "add_tags": ["assigned"]
  }
}
```

**Ответ:**

```json
{
  "id": 3001,
  "ref": 25,
  "subject": "Login form shows 500 error on Safari",
  "assigned_to": 102,
  "status": 2,
  "tags": ["bug", "safari", "frontend", "urgent", "assigned"],
  "modified_date": "2024-06-15T11:05:00Z"
}
```

#### 3.3. Добавление комментария (через append_description)

**Запрос:**

```json
{
  "name": "taiga_issues_update",
  "arguments": {
    "issue_id": 3001,
    "append_description": "\n\n## Update 2024-06-15\nFound the issue: Safari sends different User-Agent string.\nWorking on fix.",
    "add_tags": ["in-progress"]
  }
}
```

**Ответ:**

```json
{
  "id": 3001,
  "ref": 25,
  "subject": "Login form shows 500 error on Safari",
  "description": "## Bug Description\n...\n\n## Update 2024-06-15\nFound the issue: Safari sends different User-Agent string.\nWorking on fix.",
  "tags": ["bug", "safari", "frontend", "urgent", "assigned", "in-progress"]
}
```

#### 3.4. Закрытие issue

**Запрос:**

```json
{
  "name": "taiga_issues_update",
  "arguments": {
    "issue_id": 3001,
    "status": "Done",
    "append_description": "\n\n## Resolution\nFixed by normalizing User-Agent parsing.\nDeployed in v1.2.3.",
    "add_tags": ["resolved", "deployed"]
  }
}
```

**Ответ:**

```json
{
  "id": 3001,
  "ref": 25,
  "subject": "Login form shows 500 error on Safari",
  "status": 3,
  "tags": ["bug", "safari", "frontend", "urgent", "assigned", "in-progress", "resolved", "deployed"]
}
```

---

## Сценарий 4: Управление эпиками

### Цель

Создать эпик, привязать к нему истории и отслеживать прогресс.

### Шаги

#### 4.1. Создание эпика

**Запрос (через Action Proxy):**

```bash
curl -X POST -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 123,
    "subject": "Authentication System",
    "description": "Complete OAuth2 + JWT authentication flow",
    "status": "New",
    "color": "#999999",
    "tags": ["epic", "auth"]
  }' \
  "$TAIGA_PROXY_BASE_URL/actions/create_epic"
```

**Ответ:**

```json
{
  "epic": {
    "id": 4001,
    "ref": 10,
    "subject": "Authentication System",
    "project": 123,
    "status": 1,
    "color": "#999999",
    "tags": ["epic", "auth"]
  }
}
```

#### 4.2. Создание историй в эпике

**Запрос:**

```json
{
  "name": "taiga_stories_create",
  "arguments": {
    "project_id": 123,
    "subject": "As a user, I want to login with Google",
    "description": "OAuth2 login with Google provider",
    "status": "New",
    "tags": ["auth", "google"]
  }
}
```

**Ответ:**

```json
{
  "id": 1002,
  "ref": 51,
  "subject": "As a user, I want to login with Google",
  "project": 123,
  "status": 1
}
```

#### 4.3. Привязка истории к эпику

**Запрос:**

```json
{
  "name": "taiga_epics_add_user_story",
  "arguments": {
    "epic_id": 4001,
    "user_story_id": 1002
  }
}
```

**Ответ:**

```json
{
  "link": {
    "epic": 4001,
    "user_story": 1002,
    "created_date": "2024-06-15T12:00:00Z"
  }
}
```

#### 4.4. Получение прогресса эпика

**Запрос:**

```json
{
  "name": "taiga_stories_list",
  "arguments": {
    "project_id": 123,
    "epic_id": 4001
  }
}
```

**Ответ:**

```json
[
  {
    "id": 1002,
    "ref": 51,
    "subject": "As a user, I want to login with Google",
    "status": 1,
    "status_extra_info": {"name": "New", "color": "#999999"}
  }
]
```

---

## Сценарий 5: Массовое обновление задач

### Цель

Изменить статус нескольких задач одновременно.

### Шаги

#### 5.1. Получение списка задач

**Запрос:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "project_id": 123,
    "status": "New",
    "page_size": 100
  }
}
```

**Ответ:**

```json
{
  "tasks": [
    {"id": 2003, "ref": 17, "subject": "Setup database migrations", "status": 1},
    {"id": 2004, "ref": 18, "subject": "Configure logging", "status": 1}
  ],
  "pagination": {"page": 1, "page_size": 100, "total": 2, "total_pages": 1}
}
```

#### 5.2. Обновление статуса (последовательно)

**Запрос 1:**

```json
{
  "name": "taiga_tasks_update",
  "arguments": {
    "task_id": 2003,
    "status": "In progress",
    "assigned_to": 101
  }
}
```

**Запрос 2:**

```json
{
  "name": "taiga_tasks_update",
  "arguments": {
    "task_id": 2004,
    "status": "In progress",
    "assigned_to": 102
  }
}
```

### Автоматизация через Action Proxy

```python
# bulk_update.py
import requests
import json

API_KEY = "your-api-key"
BASE_URL = "https://mcp.example.com"
PROJECT_ID = 123

def update_tasks_to_in_progress():
    # Получаем задачи со статусом "New"
    response = requests.get(
        f"{BASE_URL}/actions/list_tasks",
        headers={"X-Api-Key": API_KEY},
        params={"project_id": PROJECT_ID, "status": "New"}
    )
    tasks = response.json()["tasks"]
    
    # Обновляем каждую задачу
    for task in tasks:
        update_response = requests.post(
            f"{BASE_URL}/actions/update_task",
            headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
            json={
                "task_id": task["id"],
                "status": "In progress"
            }
        )
        print(f"Updated task {task['ref']}: {update_response.status_code}")

if __name__ == "__main__":
    update_tasks_to_in_progress()
```

---

## Сценарий 6: Архивация завершённых задач

### Цель

Безопасно архивировать завершённые задачи вместо жёсткого удаления.

### Шаги

#### 6.1. Получение завершённых задач

**Запрос:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "project_id": 123,
    "status": "Done",
    "page_size": 100
  }
}
```

**Ответ:**

```json
{
  "tasks": [
    {"id": 2005, "ref": 19, "subject": "Update documentation", "status": 3},
    {"id": 2006, "ref": 20, "subject": "Fix typo in README", "status": 3}
  ],
  "pagination": {"page": 1, "page_size": 100, "total": 2, "total_pages": 1}
}
```

#### 6.2. Архивация задач

**Запрос 1:**

```json
{
  "name": "taiga_tasks_archive_or_close",
  "arguments": {
    "task_id": 2005,
    "closed_status": "Done",
    "add_archive_tag": true
  }
}
```

**Ответ:**

```json
{
  "id": 2005,
  "ref": 19,
  "subject": "Update documentation",
  "status": 3,
  "tags": ["archived-by-mcp"]
}
```

**Запрос 2:**

```json
{
  "name": "taiga_tasks_archive_or_close",
  "arguments": {
    "task_id": 2006,
    "add_archive_tag": true
  }
}
```

**Ответ:**

```json
{
  "id": 2006,
  "ref": 20,
  "subject": "Fix typo in README",
  "status": 3,
  "tags": ["archived-by-mcp"]
}
```

#### 6.3. Поиск архивированных задач

**Запрос:**

```json
{
  "name": "taiga_tasks_list",
  "arguments": {
    "project_id": 123,
    "tags": ["archived-by-mcp"],
    "page_size": 100
  }
}
```

**Ответ:**

```json
{
  "tasks": [
    {"id": 2005, "ref": 19, "subject": "Update documentation", "tags": ["archived-by-mcp"]},
    {"id": 2006, "ref": 20, "subject": "Fix typo in README", "tags": ["archived-by-mcp"]}
  ],
  "pagination": {"page": 1, "page_size": 100, "total": 2, "total_pages": 1}
}
```

---

## Сценарий 7: Интеграция с CI/CD

### Цель

Автоматически создавать задачи при падении тестов.

### Пример: GitHub Actions

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run tests
      id: test
      run: pytest
      continue-on-error: true
    
    - name: Create Taiga task on failure
      if: steps.test.outcome == 'failure'
      run: |
        curl -X POST \
          -H "X-Api-Key: ${{ secrets.TAIGA_ACTION_PROXY_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d "{
            \"project_id\": ${{ secrets.TAIGA_PROJECT_ID }},
            \"subject\": \"Tests failed on ${{ github.ref }}\",
            \"description\": \"## Failure Details\n- Branch: ${{ github.ref }}\n- Commit: ${{ github.sha }}\n- Run: ${{ github.run_id }}\n\n## Logs\nSee GitHub Actions logs for details.\",
            \"tags\": [\"ci-cd\", \"tests\", \"automated\"]
          }" \
          "${{ secrets.TAIGA_PROXY_BASE_URL }}/actions/create_task"
```

---

## Сценарий 8: Миграция между проектами

### Цель

Копировать истории из одного проекта в другой.

### Шаги

#### 8.1. Получение историй из исходного проекта

**Запрос:**

```json
{
  "name": "taiga_stories_list",
  "arguments": {
    "project_id": 123,
    "page_size": 100
  }
}
```

**Ответ:**

```json
[
  {
    "id": 1003,
    "ref": 52,
    "subject": "As a user, I want to reset password",
    "description": "Password reset flow",
    "tags": ["auth"]
  }
]
```

#### 8.2. Создание в целевом проекте

**Запрос:**

```json
{
  "name": "taiga_stories_create",
  "arguments": {
    "project_id": 456,
    "subject": "As a user, I want to reset password",
    "description": "Password reset flow\n\n_Migrated from project 123, story #52_",
    "tags": ["auth", "migrated"]
  }
}
```

**Ответ:**

```json
{
  "id": 1100,
  "ref": 1,
  "subject": "As a user, I want to reset password",
  "project": 456,
  "tags": ["auth", "migrated"]
}
```

### Автоматизация

```python
# migrate_stories.py
import requests

API_KEY = "your-api-key"
BASE_URL = "https://mcp.example.com"
SOURCE_PROJECT = 123
TARGET_PROJECT = 456

def migrate_stories():
    # Получаем истории из исходного проекта
    response = requests.get(
        f"{BASE_URL}/actions/list_stories",
        headers={"X-Api-Key": API_KEY},
        params={"project_id": SOURCE_PROJECT, "page_size": 100}
    )
    stories = response.json()["stories"]
    
    for story in stories:
        # Создаём в целевом проекте
        create_response = requests.post(
            f"{BASE_URL}/actions/create_story",
            headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
            json={
                "project_id": TARGET_PROJECT,
                "subject": story["subject"],
                "description": f"{story.get('description', '')}\n\n_Migrated from project {SOURCE_PROJECT}, story #{story['ref']}_",
                "tags": story.get("tags", []) + ["migrated"]
            }
        )
        
        if create_response.status_code == 200:
            new_story = create_response.json()["story"]
            print(f"Migrated story #{story['ref']} → #{new_story['ref']}")
        else:
            print(f"Failed to migrate story #{story['ref']}: {create_response.text}")

if __name__ == "__main__":
    migrate_stories()
```

---

## Сценарий 9: Еженедельный отчёт для stakeholders

### Цель

Сгенерировать отчёт о прогрессе проекта.

### Автоматизация

```python
# weekly_report.py
import requests
from datetime import datetime, timedelta

API_KEY = "your-api-key"
BASE_URL = "https://mcp.example.com"
PROJECT_ID = 123

def generate_weekly_report():
    # Получаем проект
    project = requests.get(
        f"{BASE_URL}/actions/get_project",
        headers={"X-Api-Key": API_KEY},
        params={"project_id": PROJECT_ID}
    ).json()["project"]
    
    # Получаем истории
    stories = requests.get(
        f"{BASE_URL}/actions/list_stories",
        headers={"X-Api-Key": API_KEY},
        params={"project_id": PROJECT_ID, "page_size": 100}
    ).json()["stories"]
    
    # Получаем задачи
    tasks = requests.get(
        f"{BASE_URL}/actions/list_tasks",
        headers={"X-Api-Key": API_KEY},
        params={"project_id": PROJECT_ID, "page_size": 100}
    ).json()["tasks"]
    
    # Статистика
    total_stories = len(stories)
    done_stories = len([s for s in stories if s.get("status") == "Done"])
    total_tasks = len(tasks)
    done_tasks = len([t for t in tasks if t.get("status") == "Done"])
    
    report = f"""
# Weekly Report: {project['name']}

**Period:** {datetime.now() - timedelta(days=7)} to {datetime.now()}

## Summary
- **Total Stories:** {total_stories}
- **Completed Stories:** {done_stories} ({done_stories/total_stories*100:.1f}%)
- **Total Tasks:** {total_tasks}
- **Completed Tasks:** {done_tasks} ({done_tasks/total_tasks*100:.1f}%)

## In Progress
"""
    
    for story in stories:
        if story.get("status") == "In progress":
            report += f"- #{story['ref']}: {story['subject']}\n"
    
    report += "\n## Recently Completed\n"
    
    for story in stories:
        if story.get("status") == "Done":
            report += f"- #{story['ref']}: {story['subject']}\n"
    
    return report

if __name__ == "__main__":
    print(generate_weekly_report())
```

---

## Сценарий 10: Обработка конфликтов версий

### Цель

Корректно обработать ошибку optimistic locking (409 Conflict).

### Проблема

```json
{
  "name": "taiga_stories_update",
  "arguments": {
    "user_story_id": 1001,
    "status": "Done",
    "version": 3
  }
}
```

**Ошибка:**

```json
{
  "error": "Conflict updating user story 1001: latest version is 5"
}
```

### Решение

```python
# safe_update.py
import requests

API_KEY = "your-api-key"
BASE_URL = "https://mcp.example.com"

def safe_update_story(story_id, updates, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Получаем актуальную версию
            story = requests.get(
                f"{BASE_URL}/actions/get_story",
                headers={"X-Api-Key": API_KEY},
                params={"story_id": story_id}
            ).json()["story"]
            
            # Обновляем с актуальной версией
            updates["story_id"] = story_id
            updates["version"] = story["version"]
            
            response = requests.post(
                f"{BASE_URL}/actions/update_story",
                headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
                json=updates
            )
            
            if response.status_code == 200:
                return response.json()
            elif "Conflict" in response.text:
                print(f"Conflict on attempt {attempt + 1}, retrying...")
                continue
            else:
                raise Exception(f"Update failed: {response.text}")
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Error on attempt {attempt + 1}: {e}")
    
    raise Exception("Max retries exceeded")

# Использование
result = safe_update_story(
    1001,
    {"status": "Done", "add_tags": ["completed"]}
)
print(f"Updated story: {result}")
```

---

## Чек-лист типовых операций

### Ежедневно

- [ ] Проверить задачи в работе (`taiga_tasks_list` with `status="In progress"`)
- [ ] Проверить просроченные задачи (`taiga_tasks_list` with `due_date` filter)
- [ ] Обновить статус выполненных задач

### Еженедельно

- [ ] Сгенерировать отчёт о прогрессе
- [ ] Проверить завершённые истории
- [ ] Архивировать закрытые задачи (`taiga_tasks_archive_or_close`)
- [ ] Обновить спринт/веху

### По мере необходимости

- [ ] Создать новые истории из обсуждений
- [ ] Создать задачи для историй
- [ ] Назначить исполнителей
- [ ] Обновить приоритеты
- [ ] Связать истории с эпиками
