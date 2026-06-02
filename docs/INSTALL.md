# Установка и развёртывание Taiga MCP в VS Code + OpenCode

Этот документ описывает развёртывание MCP-сервера Taiga с нуля в среде VS Code + OpenCode. Инструкция основана на реальном опыте интеграции и включает известные проблемы с решениями.

---

## 1. Предварительные требования

| Компонент | Версия / Требование |
|-----------|---------------------|
| Docker | 20.10+ |
| VS Code | Последняя стабильная |
| OpenCode Extension | Установлен из marketplace |
| Git | 2.30+ |
| Аккаунт Taiga | Cloud (taiga.io) или self-hosted |

**Важно:** Убедитесь, что порт `8010` свободен на локальной машине. Если занят — замените `8010` на другой во всех командах и конфигах.

---

## 2. Клонирование и подготовка

### 2.1. Клонировать репозиторий

Рекомендуется использовать форк с исправлениями багов, обнаруженных при интеграции:

```bash
git clone https://github.com/kononeer/taiga-mcp-full-fetch.git
cd taiga-mcp-full-fetch
```

**Что исправлено в форке по сравнению с upstream:**
- `json.dumps()` для list-инструментов — предотвращает разбиение MCP SDK Python-списка на отдельные `TextContent`
- Автопагинация `taiga_stories_list` и `taiga_tasks_list` — без параметра `page` подгружаются все страницы
- `_extract_tag_names()` — корректная обработка формата тегов Taiga `[['tag', null], ...]` в `add_tags`
- Исправлены несостыковки портов в документации
- Добавлен `.env.example`

### 2.2. Создать файл окружения

```bash
cp .env.example .env
```

Заполните `.env` (реальные значения, этот файл **не попадает в git**):

```env
# Обязательные
TAIGA_BASE_URL=https://api.taiga.io
TAIGA_USERNAME=your-email@example.com
TAIGA_PASSWORD=your-password

# Опциональные, но рекомендуемые
TAIGA_PROJECT_ID=1755388
TAIGA_PROJECT_SLUG=your-project-slug
ACTION_PROXY_API_KEY=change-me-32-char-random-string

# Безопасность
DESTRUCTIVE_ENABLED=false
```

**Параметры:**
- `TAIGA_BASE_URL` — `https://api.taiga.io` для облака или `https://taiga.your-company.com` для self-hosted
- `TAIGA_PROJECT_ID` / `TAIGA_PROJECT_SLUG` — позволяют не указывать `project_id` в каждом вызове инструмента
- `ACTION_PROXY_API_KEY` — случайная строка для аутентификации REST API fallback
- `DESTRUCTIVE_ENABLED=false` — запрещает жёсткое удаление (рекомендуется для production)

---

## 3. Сборка и запуск Docker-контейнера

### 3.1. Сборка образа

```bash
docker build -t taiga-mcp:latest .
```

### 3.2. Запуск контейнера

```bash
docker run -d --name taiga-mcp \
  --env-file .env \
  -p 8010:8000 \
  --restart unless-stopped \
  taiga-mcp:latest
```

**Почему именно `-p 8010:8000`:**
- Внутри контейнера uvicorn слушает порт `8000` (см. `Dockerfile` и `CMD`)
- Снаружи (хост) мы обращаемся к порту `8010`
- Все curl-проверки и OpenCode-конфиг используют `localhost:8010`

### 3.3. Проверка запуска

```bash
# Healthcheck
curl -s http://localhost:8010/healthz
# Ожидаемый ответ: ok

# Корневой endpoint
curl -s http://localhost:8010/
# Ожидаемый ответ: Taiga MCP up
```

Если ответы не приходят — проверьте:
```bash
docker ps --filter name=taiga-mcp --format "{{.Names}} {{.Status}} {{.Ports}}"
docker logs taiga-mcp --tail 20
```

---

## 4. Настройка OpenCode в VS Code

### 4.1. Отредактировать `opencode.json`

Файл находится в корне рабочей области (рядом с `.vscode/`). Добавьте секцию `mcp`:

```json
{
  "mcp": {
    "taiga": {
      "type": "remote",
      "url": "http://localhost:8010/sse/",
      "enabled": true
    }
  },
  "agent": {
    "build": {
      "permission": {
        "mcp": "allow"
      }
    }
  }
}
```

**⚠️ Критически важно — используйте SSE, а не Streamable HTTP:**

| Транспорт | URL | Статус с OpenCode |
|-----------|-----|-------------------|
| SSE | `http://localhost:8010/sse/` | ✅ Работает стабильно |
| Streamable HTTP | `http://localhost:8010/mcp/` | ❌ Не работает — OpenCode не передаёт `mcp-session-id` между запросами |

Streamable HTTP требует, чтобы клиент сначала отправил `initialize`, получил `mcp-session-id` из ответа, а затем передавал его в заголовке каждого последующего запроса. Текущая версия OpenCode MCP-клиента этого не делает, поэтому все запросы возвращают `404 Session not found`.

### 4.2. Перезапустить VS Code

**Обязательно полностью перезапустите VS Code** (`Ctrl+Shift+P` → `Developer: Reload Window` или закройте и откройте заново).

**Почему:** OpenCode кэширует схему MCP-инструментов при подключении. Если вы изменили URL, пересобрали контейнер или обновили код сервера — без перезапуска VS Code агент будет использовать старую схему и/или старое подключение.

---

## 5. Проверка интеграции

После перезапуска VS Code агент должен получить доступ к MCP-инструментам Taiga. Выполните проверку в чате OpenCode:

### 5.1. Список проектов

```
Вызови taiga_projects_list и покажи результат
```

Ожидаемый результат:
```python
[{"id": 1755388, "name": "Lowcode Platform", "slug": "kononeer-lowcode-platform"}]
```

### 5.2. Список stories (проверка автопагинации)

```
Вызови taiga_stories_list с project_id=1755388 и скажи, сколько всего stories
```

Ожидаемый результат: число больше 50 (в нашем проекте 194). Если вернулось ровно 30 — значит, используется старая версия сервера без автопагинации.

### 5.3. Проверка парсинга JSON

**⚠️ Важно:** все list-инструменты возвращают JSON-строку (`str`), а не Python-список. Правильный код:

```python
import json

raw = taiga_stories_list(project_id=1755388)
stories = json.loads(raw)  # ✅ правильно

# Неправильно (устаревший формат):
# stories = raw  # ❌ это строка, не list
```

### 5.4. Проверка add_tags

```
Создай тестовую story с тегом ["test"], затем обнови её через taiga_stories_update с add_tags=["verified"]
```

Если обновление проходит без ошибки `unhashable type: 'list'` — значит, форк с исправлением работает корректно.

**Почему это важно:** Taiga API возвращает теги в формате `[['test', null], ['verified', null]]` (список пар `[tag_name, color]`). Базовая версия сервера пыталась выполнить `set()` на этом списке, что приводило к ошибке, так как списки нельзя хешировать. В форке добавлена нормализация через `_extract_tag_names()`.

---

## 6. Полное обновление (пересборка с нуля)

Если вы внесли изменения в код или хотите гарантированно чистое состояние:

```bash
# 1. Остановить и удалить старый контейнер
docker stop taiga-mcp
docker rm taiga-mcp

# 2. Пересобрать образ
docker build -t taiga-mcp:latest .

# 3. Запустить новый контейнер
docker run -d --name taiga-mcp \
  --env-file .env \
  -p 8010:8000 \
  --restart unless-stopped \
  taiga-mcp:latest

# 4. Проверить
curl -s http://localhost:8010/healthz  # → ok

# 5. Перезапустить VS Code (обязательно!)
```

---

## 7. Action Proxy — REST API fallback

Если MCP-инструменты временно недоступны (например, проблема с транспортом), используйте Action Proxy напрямую:

```bash
# Получить API-ключ из .env
source .env

# Список проектов
curl -s -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  http://localhost:8010/actions/list_projects

# Список stories (без автопагинации — только 1 страница)
curl -s -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "http://localhost:8010/actions/list_stories?project_id=1755388&page_size=100"

# Создать story
curl -s -X POST -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id":1755388,"subject":"New story","tags":["backend"]}' \
  http://localhost:8010/actions/create_story
```

**Различия Action Proxy и MCP:**
- Action Proxy не делает автопагинацию — используйте `page` и `page_size`
- Action Proxy возвращает чистый JSON, не требуя `json.loads()`
- Action Proxy доступен всегда, независимо от состояния MCP-сессии

---

## 8. Известные проблемы и решения

### 8.1. "Session not found" или 404 на /mcp/

**Причина:** OpenCode отправляет запросы на Streamable HTTP (`/mcp/`) без заголовка `mcp-session-id`.

**Решение:** Используйте SSE (`/sse/`) в `opencode.json`.

### 8.2. Инструмент возвращает только 1 элемент вместо полного списка

**Причина:** MCP SDK Python разбивает возвращаемый Python-`list` на отдельные `TextContent` объекты. OpenCode берёт только первый.

**Решение:** В форке все list-инструменты возвращают `json.dumps(result)` (строку), которую нужно парсить через `json.loads()`. Убедитесь, что используете форк `kononeer/taiga-mcp-full-fetch`.

### 8.3. "unhashable type: 'list'" при использовании add_tags

**Причина:** Taiga возвращает теги как `[['tag', null], ...]`, а код делает `set()` на списке списков.

**Решение:** Используйте форк с `_extract_tag_names()`.

### 8.4. Изменения в коде не применяются

**Причина:** OpenCode кэширует схему инструментов при подключении к MCP-серверу.

**Решение:** Перезапустите VS Code полностью.

### 8.5. Контейнер запущен, но healthcheck не отвечает

**Причина:** Порт маппинга неверный (например, `8010:8010` вместо `8010:8000`).

**Решение:** Проверьте `docker ps` — должен быть `0.0.0.0:8010->8000/tcp`. В `docker run` используйте `-p 8010:8000`.

---

## 9. Структура репозитория

```
taiga-mcp/
├── app.py                    # Основной сервер (FastMCP + Starlette)
├── taiga_client.py           # Клиент к Taiga REST API
├── Dockerfile                # Инструкция сборки образа
├── docker-compose.yml        # Альтернативный запуск
├── requirements.txt          # Python-зависимости
├── .env.example              # Шаблон переменных окружения
├── .gitignore                # Исключает .env, но сохраняет .env.example
├── README.md                 # Общее описание и быстрый старт
├── opencode.json             # Пример конфигурации OpenCode
└── docs/
    ├── INSTALL.md            # ← Этот документ
    ├── API.md                # Справочник по MCP-инструментам
    └── GUIDE.md              # Примеры использования и деплой
```

---

## 10. Ссылки

- **Форк с исправлениями:** https://github.com/kononeer/taiga-mcp-full-fetch
- **Upstream:** https://github.com/OFFSET3/taiga-mcp
- **Taiga:** https://taiga.io/
- **MCP Specification:** https://modelcontextprotocol.io/
