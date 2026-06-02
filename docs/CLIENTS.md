# Интеграция с MCP-клиентами

## Обзор

Taiga MCP Server поддерживает стандартный Model Context Protocol (MCP) и может быть интегрирован с различными AI-ассистентами и IDE. Этот раздел описывает настройку популярных MCP-клиентов.

## Поддерживаемые клиенты

| Клиент | Транспорт | Особенности |
|--------|-----------|-------------|
| **ChatGPT (Custom GPT)** | Streamable HTTP | Встроенная поддержка MCP в GPT Builder |
| **Claude Desktop** | SSE / stdio | Нативная поддержка MCP |
| **VS Code + Cline** | SSE | Расширение с поддержкой MCP |
| **Cursor** | SSE | Встроенная поддержка MCP |
| **Windsurf** | SSE | Поддержка через конфигурацию |
| **Goose** | SSE / stdio | CLI-инструмент с MCP |

## ChatGPT (Custom GPT)

### Требования

- Подписка ChatGPT Plus / Enterprise
- Доступ к GPT Builder
- Развёрнутый Taiga MCP Server с публичным URL

### Настройка

#### 1. Подготовка сервера

Убедитесь, что сервер доступен по HTTPS:

```bash
# Проверка доступности
curl https://mcp.example.com/healthz
# Ожидается: ok
```

#### 2. Создание Custom GPT

1. Откройте [ChatGPT](https://chat.openai.com/)
2. Перейдите в **Explore** → **Create a GPT**
3. Нажмите **Configure**
4. Прокрутите до раздела **Actions**
5. Нажмите **Add** в секции **Model Context Protocol**

#### 3. Настройка MCP

```
Name: Taiga Project Manager
Description: Manage Taiga projects through MCP

MCP Server URL: https://mcp.example.com/mcp
```

**Важно:**
- Используйте `/mcp` endpoint (Streamable HTTP)
- Не добавляйте заголовки или тело запроса (если нет дополнительной аутентификации)
- URL должен быть доступен из интернета

#### 4. Тестирование

Сохраните GPT и протестируйте:

```
User: List all projects
GPT: [Вызывает taiga_projects_list]
     Here are your projects:
     1. Backend API (backend-api)
     2. Frontend App (frontend-app)
```

#### 5. Промпт для GPT

Рекомендуемый системный промпт:

```
You are a Taiga project management assistant. You help users manage their projects, epics, user stories, tasks, and issues through the Taiga MCP server.

Always:
1. Start by getting an overview of available projects if not specified
2. Confirm destructive actions before executing
3. Provide clear summaries of changes
4. Use archive_or_close instead of delete when possible

Available operations:
- List and search projects, epics, stories, tasks, issues
- Create new stories, tasks, and issues
- Update existing items (status, assignee, tags, description)
- Archive completed items safely
```

### Ограничения

- **Таймаут:** ChatGPT имеет таймаут на выполнение инструментов (обычно 45 секунд)
- **Пагинация:** Большие списки могут требовать нескольких вызовов
- **Контекст:** История разговора ограничена контекстным окном модели

---

## Claude Desktop

### Требования

- Claude Desktop App (macOS / Windows)
- Аккаунт Anthropic

### Настройка

#### 1. Конфигурационный файл

Claude Desktop использует JSON-конфигурацию для MCP-серверов:

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

#### 2. Добавление Taiga MCP

```json
{
  "mcpServers": {
    "taiga": {
      "command": "python",
      "args": [
        "/path/to/streamable_client.py",
        "https://mcp.example.com/mcp"
      ],
      "env": {
        "TAIGA_BASE_URL": "https://taiga.example.com",
        "TAIGA_USERNAME": "service-account",
        "TAIGA_PASSWORD": "password",
        "ACTION_PROXY_API_KEY": "api-key"
      }
    }
  }
}
```

**Альтернатива с npx (если опубликован как npm-пакет):**

```json
{
  "mcpServers": {
    "taiga": {
      "command": "npx",
      "args": [
        "-y",
        "@offset3/taiga-mcp-client",
        "--url",
        "https://mcp.example.com/mcp"
      ]
    }
  }
}
```

#### 3. Перезапуск Claude Desktop

После изменения конфигурации полностью закройте и откройте Claude Desktop.

#### 4. Проверка

В чате Claude появится 🔨 иконка, указывающая на доступные инструменты.

Тестовый запрос:

```
List all my Taiga projects
```

Claude должен вызвать `taiga_projects_list` и показать результат.

### Troubleshooting

#### Инструменты не появляются

1. Проверьте конфигурационный файл на валидность JSON
2. Убедитесь, что путь к скрипту корректный
3. Проверьте логи Claude:
   - **macOS:** `~/Library/Logs/Claude/`
   - **Windows:** `%APPDATA%\Claude\logs\`

#### Ошибка подключения

```bash
# Проверьте доступность сервера
curl https://mcp.example.com/healthz

# Проверьте MCP endpoint
curl -H "Accept: application/json, text/event-stream" \
  https://mcp.example.com/mcp/
```

---

## VS Code + Cline

### Требования

- VS Code 1.90+
- Расширение [Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)

### Настройка

#### 1. Установка Cline

1. Откройте VS Code
2. Перейдите в Extensions (Ctrl+Shift+X)
3. Найдите "Cline" и установите

#### 2. Настройка MCP в Cline

1. Откройте панель Cline (Ctrl+Shift+P → "Cline: Open")
2. Нажмите на ⚙️ (Settings)
3. Перейдите в раздел **MCP Servers**
4. Нажмите **Add Server**

```json
{
  "name": "taiga",
  "transport": "sse",
  "url": "https://mcp.example.com/sse/",
  "headers": {
    "Authorization": "Bearer optional-token"
  }
}
```

**Или через Streamable HTTP:**

```json
{
  "name": "taiga",
  "transport": "http",
  "url": "https://mcp.example.com/mcp/",
  "headers": {
    "Accept": "application/json, text/event-stream"
  }
}
```

#### 3. Использование

В чате Cline:

```
@taiga List all projects
```

Cline автоматически вызовет соответствующий инструмент.

### Особенности

- **Inline suggestions:** Cline может предлагать вызовы инструментов на основе контекста
- **Code generation:** Можно генерировать код на основе задач из Taiga
- **File integration:** Связь между задачами и файлами в проекте

---

## Cursor

### Требования

- Cursor IDE (0.40+)
- Подписка Cursor Pro (для некоторых функций)

### Настройка

#### 1. Открытие настроек MCP

1. Откройте Cursor
2. Перейдите в **Settings** (Ctrl+,)
3. Найдите раздел **MCP Servers**
4. Нажмите **Add MCP Server**

#### 2. Конфигурация

```json
{
  "name": "taiga",
  "type": "sse",
  "url": "https://mcp.example.com/sse/"
}
```

**Или для Streamable HTTP:**

```json
{
  "name": "taiga",
  "type": "http",
  "url": "https://mcp.example.com/mcp/",
  "headers": {
    "Accept": "application/json, text/event-stream"
  }
}
```

#### 3. Использование

В чате Cursor (Cmd+L):

```
Show me all tasks assigned to John
```

Cursor автоматически определит необходимые вызовы инструментов.

### Composer Integration

Cursor Composer может использовать MCP-инструменты для:

- Создания задач из обсуждений кода
- Обновления статуса при завершении работы
- Связи коммитов с задачами

---

## Windsurf

### Требования

- Windsurf IDE
- Аккаунт Codeium

### Настройка

#### 1. Открытие Cascade

1. Откройте Windsurf
2. Нажмите **Cascade** (боковая панель)
3. Нажмите на ⚙️ в верхнем правом углу

#### 2. Добавление MCP-сервера

```json
{
  "mcpServers": {
    "taiga": {
      "url": "https://mcp.example.com/sse/",
      "type": "sse"
    }
  }
}
```

#### 3. Использование

В чате Cascade:

```
Create a new user story for OAuth2 implementation
```

Cascade вызовет `taiga_stories_create` с соответствующими параметрами.

---

## Goose

### Требования

- Goose CLI
- Rust toolchain (для сборки)

### Установка

```bash
# Установка Goose
brew install goose  # macOS
# или
cargo install goose  # из исходников
```

### Настройка

#### 1. Конфигурация Goose

```bash
# Инициализация конфигурации
goose configure

# Добавление MCP-сервера
goose mcp add taiga \
  --url https://mcp.example.com/mcp/ \
  --type http
```

#### 2. Использование

```bash
# Запуск сессии
goose session

# В интерактивном режиме:
> List all my projects
> Create a new task for user story 123
> Update task 456 status to Done
```

### Расширения

Goose поддерживает создание кастомных расширений:

```rust
// src/extensions/taiga.rs
use goose::prelude::*;

#[derive(Debug)]
pub struct TaigaExtension;

#[async_trait]
impl Extension for TaigaExtension {
    fn name(&self) -> &str {
        "taiga"
    }
    
    async fn initialize(&self, config: &Config) -> Result<()> {
        // Инициализация подключения к Taiga MCP
        Ok(())
    }
}
```

---

## Прямая интеграция через Python

### Использование mcp Python SDK

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Параметры подключения к локальному серверу
server_params = StdioServerParameters(
    command="python",
    args=["-m", "taiga_mcp_server"],
    env={
        "TAIGA_BASE_URL": "https://taiga.example.com",
        "TAIGA_USERNAME": "service-account",
        "TAIGA_PASSWORD": "password",
    }
)

async def use_taiga_mcp():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Инициализация
            await session.initialize()
            
            # Получение списка инструментов
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Вызов инструмента
            result = await session.call_tool(
                "taiga_projects_list",
                arguments={"search": "backend"}
            )
            print(f"Projects: {result}")

# Запуск
import asyncio
asyncio.run(use_taiga_mcp())
```

### Использование HTTP-клиента

```python
import requests
import json

class TaigaMCPClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'X-Api-Key': api_key
            })
    
    def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Вызов MCP-инструмента через Action Proxy."""
        
        # Маппинг инструментов на endpoints
        tool_mapping = {
            'taiga_projects_list': ('GET', '/actions/list_projects'),
            'taiga_projects_get': ('GET', '/actions/get_project'),
            'taiga_stories_list': ('GET', '/actions/list_stories'),
            'taiga_stories_create': ('POST', '/actions/create_story'),
            'taiga_stories_update': ('POST', '/actions/update_story'),
            'taiga_tasks_list': ('GET', '/actions/list_tasks'),
            'taiga_tasks_create': ('POST', '/actions/create_task'),
            'taiga_tasks_update': ('POST', '/actions/update_task'),
        }
        
        method, endpoint = tool_mapping.get(tool_name)
        if not method:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        url = f"{self.base_url}{endpoint}"
        
        if method == 'GET':
            response = self.session.get(url, params=arguments)
        else:
            response = self.session.post(url, json=arguments)
        
        response.raise_for_status()
        return response.json()
    
    def list_projects(self, search: str = None) -> list:
        """Получение списка проектов."""
        result = self.call_tool('taiga_projects_list', {'search': search})
        return result.get('projects', [])
    
    def create_story(self, project_id: int, subject: str, **kwargs) -> dict:
        """Создание пользовательской истории."""
        arguments = {
            'project_id': project_id,
            'subject': subject,
            **kwargs
        }
        result = self.call_tool('taiga_stories_create', arguments)
        return result.get('story', {})

# Использование
client = TaigaMCPClient(
    base_url='https://mcp.example.com',
    api_key='your-api-key'
)

# Получение проектов
projects = client.list_projects(search='backend')
print(f"Found {len(projects)} projects")

# Создание истории
story = client.create_story(
    project_id=123,
    subject='As a user, I want to login',
    description='OAuth2 login implementation',
    tags=['auth', 'frontend']
)
print(f"Created story: {story['ref']}")
```

---

## Интеграция с фреймворками

### LangChain

```python
from langchain.tools import BaseTool
from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI

class TaigaListProjectsTool(BaseTool):
    name = "taiga_projects_list"
    description = "List all Taiga projects"
    
    def _run(self, search: str = None):
        import requests
        response = requests.get(
            "https://mcp.example.com/actions/list_projects",
            headers={"X-Api-Key": "your-api-key"},
            params={"search": search}
        )
        return response.json()
    
    async def _arun(self, search: str = None):
        raise NotImplementedError

# Создание агента
tools = [TaigaListProjectsTool()]
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

# Использование
agent.run("List all my backend projects")
```

### LlamaIndex

```python
from llama_index.tools import FunctionTool
from llama_index.agent import OpenAIAgent

def taiga_list_projects(search: str = None) -> str:
    """List Taiga projects."""
    import requests
    response = requests.get(
        "https://mcp.example.com/actions/list_projects",
        headers={"X-Api-Key": "your-api-key"},
        params={"search": search}
    )
    return json.dumps(response.json())

# Создание инструмента
tool = FunctionTool.from_defaults(
    fn=taiga_list_projects,
    name="taiga_projects_list",
    description="List all Taiga projects with optional search filter"
)

# Создание агента
agent = OpenAIAgent.from_tools([tool], verbose=True)

# Использование
response = agent.chat("Show me all projects")
```

---

## Безопасность при интеграции

### Рекомендации

1. **HTTPS:** Всегда используйте HTTPS для публичных endpoint'ов
2. **API-ключи:** Храните ключи в переменных окружения или менеджерах секретов
3. **CORS:** Настройте CORS если MCP-сервер доступен из браузера
4. **Rate limiting:** Добавьте ограничение запросов на уровне reverse proxy
5. **Логирование:** Логируйте все вызовы инструментов

### Пример Nginx конфигурации

```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req_zone $binary_remote_addr zone=mcp:10m rate=10r/s;
        limit_req zone=mcp burst=20 nodelay;
        
        # CORS
        add_header Access-Control-Allow-Origin "https://chat.openai.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Api-Key" always;
    }
}
```

---

## Troubleshooting интеграций

### ChatGPT: "Unable to connect to MCP server"

1. Проверьте доступность URL из интернета:
   ```bash
   curl -I https://mcp.example.com/healthz
   ```

2. Проверьте SSL-сертификат:
   ```bash
   openssl s_client -connect mcp.example.com:443
   ```

3. Убедитесь, что `/mcp/` endpoint возвращает корректные заголовки:
   ```bash
   curl -v -H "Accept: application/json, text/event-stream" \
     https://mcp.example.com/mcp/
   ```

### Claude Desktop: Инструменты не появляются

1. Проверьте логи:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   
   # Windows
   type %APPDATA%\Claude\logs\mcp*.log
   ```

2. Проверьте валидность JSON конфигурации:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

3. Убедитесь, что скрипт client имеет права на выполнение:
   ```bash
   chmod +x /path/to/streamable_client.py
   ```

### VS Code + Cline: Ошибка подключения

1. Проверьте URL в конфигурации
2. Убедитесь, что нет firewall блокировок
3. Проверьте CORS заголовки

### Общие проблемы

#### `Not Acceptable: Client must accept text/event-stream`

**Причина:** Неверный заголовок Accept.

**Решение:** Убедитесь, что клиент отправляет:
```
Accept: application/json, text/event-stream
```

#### `Session terminated`

**Причина:** Редирект или прокси удаляет заголовки.

**Решение:**
- Используйте `/mcp/` (с trailing slash)
- Настройте прокси для сохранения заголовков
- Отключите автоматические редиректы

#### `Invalid API key`

**Причина:** Неверный или отсутствующий X-Api-Key.

**Решение:** Проверьте конфигурацию Action Proxy и заголовки запроса.

---

## Сравнение клиентов

| Критерий | ChatGPT | Claude Desktop | VS Code + Cline | Cursor | Windsurf | Goose |
|----------|---------|----------------|-----------------|--------|----------|-------|
| **Установка** | Простая | Простая | Средняя | Простая | Простая | Сложная |
| **Транспорт** | HTTP | stdio/SSE | SSE | SSE | SSE | HTTP/stdio |
| **UI** | Web | Desktop | IDE | IDE | IDE | CLI |
| **Контекст** | Разговор | Разговор | Код + чат | Код + чат | Код + чат | CLI |
| **Автоматизация** | Нет | Нет | Да | Да | Да | Да |
| **Лучшее для** | Менеджеров | Разработчиков | Разработчиков | Разработчиков | Разработчиков | DevOps |

## Рекомендации по выбору клиента

- **Для менеджеров проектов:** ChatGPT Custom GPT (простой веб-интерфейс)
- **Для разработчиков:** Claude Desktop или Cursor (интеграция с кодом)
- **Для командной работы:** VS Code + Cline (общий IDE)
- **Для автоматизации:** Goose (CLI + скрипты)
- **Для прототипирования:** Прямая HTTP-интеграция через Python
