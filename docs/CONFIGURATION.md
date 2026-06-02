# Конфигурация

## Переменные окружения

### Обязательные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TAIGA_BASE_URL` | Базовый URL Taiga API | `https://taiga.example.com` |
| `TAIGA_USERNAME` | Имя пользователя service account | `mcp-service` |
| `TAIGA_PASSWORD` | Пароль service account | `secure-password` |

### Опциональные

| Переменная | Описание | По умолчанию | Пример |
|------------|----------|--------------|--------|
| `TAIGA_PROJECT_ID` | ID проекта по умолчанию | — | `123` |
| `TAIGA_PROJECT_SLUG` | Slug проекта по умолчанию | — | `my-project` |
| `ACTION_PROXY_API_KEY` | API-ключ для Action Proxy | — | `random-api-key-123` |
| `MCP_URL` | URL MCP-сервера для тестов | — | `https://mcp.example.com/mcp` |
| `TAIGA_PROXY_BASE_URL` | Базовый URL для Action Proxy | — | `https://mcp.example.com` |
| `DESTRUCTIVE_ENABLED` | Включить жёсткое удаление | `false` | `true` |

### Формат URL

**Taiga Base URL** поддерживает два формата:

```
# Формат 1: Корень сайта (рекомендуется)
TAIGA_BASE_URL=https://taiga.example.com

# Формат 2: API root
TAIGA_BASE_URL=https://taiga.example.com/api/v1
```

Сервер автоматически нормализует URL, добавляя `/api/v1` если отсутствует.

## Файл конфигурации

### Шаблон (.env.example)

```bash
# Taiga Connection
TAIGA_BASE_URL=https://taiga.example.com
TAIGA_USERNAME=service-account
TAIGA_PASSWORD=your-password

# Default Project (optional)
TAIGA_PROJECT_ID=123
TAIGA_PROJECT_SLUG=my-project

# Action Proxy (optional)
ACTION_PROXY_API_KEY=your-random-api-key

# Testing (optional)
MCP_URL=https://your-domain.example/mcp
TAIGA_PROXY_BASE_URL=https://your-domain.example

# Destructive Operations (optional, default: false)
DESTRUCTIVE_ENABLED=false
```

### Загрузка конфигурации

```python
from dotenv import load_dotenv

# Автоматически загружает .env файл
load_dotenv()

# Или явно указать путь
load_dotenv("/path/to/.env")
```

## Service Account

### Создание в Taiga

1. **Админ-панель Taiga:**
   - Перейдите в Admin → Users
   - Создайте нового пользователя с ролью **Staff**

2. **Права доступа:**
   - Добавьте service account в проекты как **Member**
   - Назначьте роль с необходимыми правами (обычно **Back** или **Product Owner**)

3. **Рекомендуемые права:**
   - Просмотр проектов
   - Создание/редактирование историй, задач, эпиков
   - Удаление (если `DESTRUCTIVE_ENABLED=true`)

### Безопасность

- **Выделенный аккаунт:** Не используйте личный аккаунт
- **Сложный пароль:** Минимум 16 символов, смешанные регистры, цифры, спецсимволы
- **Ротация:** Меняйте пароль каждые 90 дней
- **Мониторинг:** Отслеживайте активность service account

## Настройка проекта по умолчанию

Если указаны `TAIGA_PROJECT_ID` или `TAIGA_PROJECT_SLUG`, многие инструменты могут работать без явного указания `project_id`:

```python
async def _require_project_id(client, project_id: int | None = None) -> int:
    if project_id is not None:
        return project_id
    
    # Проверяем env переменные
    env_id = os.getenv("TAIGA_PROJECT_ID")
    if env_id:
        return int(env_id)
    
    env_slug = os.getenv("TAIGA_PROJECT_SLUG")
    if env_slug:
        project = await client.get_project_by_slug(env_slug)
        return project["id"]
    
    raise ValueError("project_id is required")
```

**Примеры:**

```json
// С project_id
{
  "name": "taiga_stories_list",
  "arguments": {"project_id": 123}
}

// Без project_id (используется env)
{
  "name": "taiga_stories_list",
  "arguments": {}
}
```

## Action Proxy

### Генерация API-ключа

```bash
# Случайный ключ (32 байта = 64 hex символа)
openssl rand -hex 32

# Пример вывода:
# a3f5c8e9d2b1f4e7a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b
```

### Хранение в Azure Container Apps

```bash
# Установка секрета
az containerapp secret set \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --secrets action-proxy-api-key="$(openssl rand -hex 32)"

# Привязка к переменной окружения
az containerapp update \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --set-env-vars ACTION_PROXY_API_KEY=secretref:action-proxy-api-key
```

### Хранение в Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: taiga-mcp-secrets
type: Opaque
stringData:
  taiga-username: "service-account"
  taiga-password: "secure-password"
  action-proxy-api-key: "random-api-key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taiga-mcp
spec:
  template:
    spec:
      containers:
      - name: taiga-mcp
        image: ghcr.io/johnwblack/taiga-mcp:latest
        env:
        - name: TAIGA_BASE_URL
          value: "https://taiga.example.com"
        - name: TAIGA_USERNAME
          valueFrom:
            secretKeyRef:
              name: taiga-mcp-secrets
              key: taiga-username
        - name: TAIGA_PASSWORD
          valueFrom:
            secretKeyRef:
              name: taiga-mcp-secrets
              key: taiga-password
        - name: ACTION_PROXY_API_KEY
          valueFrom:
            secretKeyRef:
              name: taiga-mcp-secrets
              key: action-proxy-api-key
```

## Деструктивные операции

### Включение

```bash
# В .env файле
DESTRUCTIVE_ENABLED=true

# Или при запуске
DESTRUCTIVE_ENABLED=true uvicorn app:app --host 0.0.0.0 --port 8010
```

### Предупреждение

⚠️ **ВНИМАНИЕ:** Включение `DESTRUCTIVE_ENABLED` позволяет:

- Полное удаление эпиков (`taiga_epics_delete`)
- Полное удаление историй (`taiga_stories_delete`)
- Полное удаление задач (`taiga_tasks_delete`)
- Полное удаление issues (`taiga_issues_delete`)

**Удалённые сущности нельзя восстановить!**

### Рекомендации

1. **Используйте `archive_or_close`** вместо удаления
2. **Включайте `DESTRUCTIVE_ENABLED`** только при необходимости
3. **Ограничьте права** service account в Taiga
4. **Логируйте** все деструктивные операции

## Проверка конфигурации

### Локальная проверка

```bash
# 1. Загрузка env
source .env

# 2. Проверка переменных
echo $TAIGA_BASE_URL
echo $TAIGA_USERNAME

# 3. Запуск сервера
uvicorn app:app --host 127.0.0.1 --port 8010

# 4. Проверка health check
curl http://127.0.0.1:8010/healthz
# Ожидается: ok

# 5. Проверка MCP
curl -H "Accept: text/event-stream" http://127.0.0.1:8010/sse/

# 6. Проверка Action Proxy
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/list_projects"
```

### Диагностика

```bash
# Проверка соединения с Taiga
python scripts/actions_proxy_client.py --pretty diagnostics

# Проверка видимости проекта
python scripts/actions_proxy_client.py diagnostics --slug my-project
```

## Troubleshooting конфигурации

### `Environment variable TAIGA_BASE_URL must be configured`

**Причина:** Отсутствует обязательная переменная окружения.

**Решение:**
```bash
# Проверьте .env файл
cat .env | grep TAIGA_BASE_URL

# Или установите явно
export TAIGA_BASE_URL=https://taiga.example.com
```

### `Taiga authentication failed with status 401`

**Причина:** Неверные учётные данные Taiga.

**Решение:**
1. Проверьте логин/пароль в `.env`
2. Убедитесь, что service account активен в Taiga
3. Проверьте, что Taiga URL доступен

### `Invalid API key`

**Причина:** Неверный или отсутствующий `X-Api-Key`.

**Решение:**
```bash
# Проверьте ключ
echo $ACTION_PROXY_API_KEY

# Проверьте заголовок в запросе
curl -v -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "$TAIGA_PROXY_BASE_URL/actions/list_projects"
```

### `Action Proxy not configured`

**Причина:** Не установлена переменная `ACTION_PROXY_API_KEY`.

**Решение:**
```bash
export ACTION_PROXY_API_KEY=$(openssl rand -hex 32)
```

## Примеры конфигураций

### Минимальная (только чтение)

```bash
TAIGA_BASE_URL=https://taiga.example.com
TAIGA_USERNAME=readonly-user
TAIGA_PASSWORD=password123
```

### Полная (все операции)

```bash
TAIGA_BASE_URL=https://taiga.example.com
TAIGA_USERNAME=service-account
TAIGA_PASSWORD=SecureP@ssw0rd!
TAIGA_PROJECT_ID=123
TAIGA_PROJECT_SLUG=my-project
ACTION_PROXY_API_KEY=a3f5c8e9d2b1f4e7a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b
MCP_URL=https://mcp.example.com/mcp
TAIGA_PROXY_BASE_URL=https://mcp.example.com
DESTRUCTIVE_ENABLED=false
```

### Для разработки

```bash
TAIGA_BASE_URL=http://localhost:8000
TAIGA_USERNAME=admin
TAIGA_PASSWORD=123123
TAIGA_PROJECT_ID=1
ACTION_PROXY_API_KEY=dev-key-123
DESTRUCTIVE_ENABLED=true
```

### Для production

```bash
TAIGA_BASE_URL=https://taiga.company.com
TAIGA_USERNAME=mcp-service@company.com
TAIGA_PASSWORD=<from-secret-manager>
TAIGA_PROJECT_ID=456
ACTION_PROXY_API_KEY=<from-secret-manager>
MCP_URL=https://mcp.company.com/mcp
TAIGA_PROXY_BASE_URL=https://mcp.company.com
DESTRUCTIVE_ENABLED=false
```
