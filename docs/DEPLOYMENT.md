# Деплой

## Обзор

Taiga MCP Server может быть развёрнут несколькими способами:

1. **Локально** — для разработки и тестирования
2. **Docker** — контейнеризация
3. **Azure Container Apps** — облачный деплой (рекомендуется)
4. **Kubernetes** — оркестрация

## Требования

### Локальный деплой

- Python 3.11+
- pip
- virtualenv (рекомендуется)

### Контейнерный деплой

- Docker 20.10+
- Docker Compose (опционально)

### Azure деплой

- Azure CLI 2.50+
- Подписка Azure
- Resource Group

## Локальный деплой

### 1. Клонирование репозитория

```bash
git clone https://github.com/OFFSET3/taiga-mcp.git
cd taiga-mcp
```

### 2. Создание виртуального окружения

```bash
# Linux/Mac
python -m venv .chat-venv
source .chat-venv/bin/activate

# Windows
python -m venv .chat-venv
.\.chat-venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Конфигурация

```bash
cp .env.example .env
# Отредактируйте .env файл
```

### 5. Запуск

```bash
# Стандартный запуск
uvicorn app:app --host 127.0.0.1 --port 8010

# С автоперезагрузкой (для разработки)
uvicorn app:app --host 127.0.0.1 --port 8010 --reload
```

### 6. Проверка

```bash
# Health check
curl http://127.0.0.1:8010/healthz

# SSE endpoint
curl -sN -H "Accept: text/event-stream" http://127.0.0.1:8010/sse/

# MCP probe
python streamable_client.py http://127.0.0.1:8010/mcp --message "hello local"
```

## Docker деплой

### Сборка образа

```bash
# Установка переменных
export CONTAINER_IMAGE=ghcr.io/johnwblack/taiga-mcp
export IMAGE_TAG=v1.1.0

# Сборка
docker build -t "$CONTAINER_IMAGE:$IMAGE_TAG" \
  -t "$CONTAINER_IMAGE:latest" .
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]
```

### Запуск контейнера

```bash
# С env файлом
docker run -d \
  --name taiga-mcp \
  -p 8010:8010 \
  --env-file .env \
  "$CONTAINER_IMAGE:$IMAGE_TAG"

# С явными переменными
docker run -d \
  --name taiga-mcp \
  -p 8010:8010 \
  -e TAIGA_BASE_URL=https://taiga.example.com \
  -e TAIGA_USERNAME=service-account \
  -e TAIGA_PASSWORD=password \
  -e ACTION_PROXY_API_KEY=api-key \
  "$CONTAINER_IMAGE:$IMAGE_TAG"
```

### Docker Compose

```yaml
version: '3.8'

services:
  taiga-mcp:
    image: ghcr.io/johnwblack/taiga-mcp:v1.1.0
    container_name: taiga-mcp
    ports:
      - "8010:8010"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

```bash
docker-compose up -d
```

## Azure Container Apps деплой

### Предварительные требования

```bash
# Установка Azure CLI
# https://docs.microsoft.com/cli/azure/install-azure-cli

# Логин
az login

# Установка расширения Container Apps
az extension add --name containerapp --upgrade
```

### Настройка переменных

```bash
# Bash
export AZURE_RESOURCE_GROUP='your-resource-group'
export AZURE_CONTAINER_APP='taiga-mcp'
export CONTAINER_IMAGE='ghcr.io/johnwblack/taiga-mcp'
export IMAGE_TAG='v1.1.0'

# PowerShell
$env:AZURE_RESOURCE_GROUP = 'your-resource-group'
$env:AZURE_CONTAINER_APP = 'taiga-mcp'
$env:CONTAINER_IMAGE = 'ghcr.io/johnwblack/taiga-mcp'
$env:IMAGE_TAG = 'v1.1.0'
```

### Создание Container App

```bash
# Создание окружения (если не существует)
az containerapp env create \
  --name taiga-mcp-env \
  --resource-group $AZURE_RESOURCE_GROUP \
  --location eastus

# Создание Container App
az containerapp create \
  --name $AZURE_CONTAINER_APP \
  --resource-group $AZURE_RESOURCE_GROUP \
  --environment taiga-mcp-env \
  --image "$CONTAINER_IMAGE:$IMAGE_TAG" \
  --target-port 8010 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi
```

### Настройка секретов

```bash
# Taiga credentials
az containerapp secret set \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --secrets \
    taiga-username="service-account" \
    taiga-password="secure-password"

# Action Proxy API Key
az containerapp secret set \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --secrets \
    action-proxy-api-key="$(openssl rand -hex 32)"
```

### Настройка переменных окружения

```bash
az containerapp update \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --set-env-vars \
    TAIGA_BASE_URL="https://taiga.example.com" \
    TAIGA_USERNAME="secretref:taiga-username" \
    TAIGA_PASSWORD="secretref:taiga-password" \
    ACTION_PROXY_API_KEY="secretref:action-proxy-api-key" \
    TAIGA_PROJECT_ID="123" \
    TAIGA_PROJECT_SLUG="my-project"
```

### Обновление ревизии

```bash
# Сборка и пуш нового образа
docker build -t "$CONTAINER_IMAGE:$IMAGE_TAG" .
docker push "$CONTAINER_IMAGE:$IMAGE_TAG"

# Обновление Container App
az containerapp update \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --image "$CONTAINER_IMAGE:$IMAGE_TAG"
```

### Автоматический деплой

```bash
# Использование helper script
python scripts/deploy_to_azure.py \
  --image "$CONTAINER_IMAGE" \
  --tag "$IMAGE_TAG" \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --container-app "$AZURE_CONTAINER_APP"

# Опции:
# --skip-build    # Пропустить сборку
# --skip-push     # Пропустить push
# --latest-tag    # Дополнительно тегнуть как latest
```

### Мониторинг

```bash
# Логи
az containerapp logs show \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --tail 50

# Метрики
az containerapp show \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --query "properties.runningStatus"
```

## Kubernetes деплой

### Namespace

```bash
kubectl create namespace taiga-mcp
```

### Secret

```bash
kubectl create secret generic taiga-mcp-secrets \
  --namespace taiga-mcp \
  --from-literal=taiga-username="service-account" \
  --from-literal=taiga-password="secure-password" \
  --from-literal=action-proxy-api-key="$(openssl rand -hex 32)"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taiga-mcp
  namespace: taiga-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: taiga-mcp
  template:
    metadata:
      labels:
        app: taiga-mcp
    spec:
      containers:
      - name: taiga-mcp
        image: ghcr.io/johnwblack/taiga-mcp:v1.1.0
        ports:
        - containerPort: 8010
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
        - name: TAIGA_PROJECT_ID
          value: "123"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8010
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8010
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: taiga-mcp
  namespace: taiga-mcp
spec:
  selector:
    app: taiga-mcp
  ports:
  - port: 80
    targetPort: 8010
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: taiga-mcp
  namespace: taiga-mcp
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - mcp.example.com
    secretName: taiga-mcp-tls
  rules:
  - host: mcp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: taiga-mcp
            port:
              number: 80
```

### Применение

```bash
kubectl apply -f k8s/
```

## GitHub Container Registry

### Аутентификация

```bash
# Создание Personal Access Token с правами read:packages, write:packages
# https://github.com/settings/tokens

# Логин в GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Публикация образа

```bash
# Тегирование
docker tag taiga-mcp:latest ghcr.io/johnwblack/taiga-mcp:v1.1.0

# Пуш
docker push ghcr.io/johnwblack/taiga-mcp:v1.1.0

# Дополнительно тег latest
docker tag taiga-mcp:latest ghcr.io/johnwblack/taiga-mcp:latest
docker push ghcr.io/johnwblack/taiga-mcp:latest
```

## CI/CD

### GitHub Actions

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:${{ github.ref_name }}
          ghcr.io/${{ github.repository }}:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy to Azure Container Apps
      run: |
        az containerapp update \
          --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
          --name ${{ secrets.AZURE_CONTAINER_APP }} \
          --image ghcr.io/${{ github.repository }}:${{ github.ref_name }}
```

## Проверка деплоя

### Health Checks

```bash
# Root endpoint
curl https://mcp.example.com/
# Ожидается: Taiga MCP up

# Health check
curl https://mcp.example.com/healthz
# Ожидается: ok

# SSE endpoint
curl -sN -H "Accept: text/event-stream" \
  https://mcp.example.com/sse/

# MCP probe
python streamable_client.py \
  https://mcp.example.com/mcp \
  --message "ping"
```

### Action Proxy

```bash
# Список проектов
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "https://mcp.example.com/actions/list_projects"

# Диагностика
curl -H "X-Api-Key: $ACTION_PROXY_API_KEY" \
  "https://mcp.example.com/actions/diagnostics"
```

### ChatGPT Integration

1. **Откройте GPT Builder**
2. **Configure → Add** (Model Context Protocol tools)
3. **Введите URL:** `https://mcp.example.com/mcp`
4. **Сохраните и протестируйте** с инструментом `echo`

## Troubleshooting деплоя

### Контейнер не запускается

```bash
# Проверка логов
docker logs taiga-mcp

# Проверка env переменных
docker exec taiga-mcp env | grep TAIGA
```

### Ошибка аутентификации в Taiga

```bash
# Проверка доступности Taiga
curl $TAIGA_BASE_URL/api/v1/projects

# Проверка учётных данных
python scripts/actions_proxy_client.py diagnostics
```

### Azure Container Apps не отвечает

```bash
# Проверка статуса
az containerapp show \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --query "properties.runningStatus"

# Просмотр логов
az containerapp logs show \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --tail 100

# Перезапуск
az containerapp revision restart \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --revision $(az containerapp show \
    --resource-group $AZURE_RESOURCE_GROUP \
    --name $AZURE_CONTAINER_APP \
    --query "properties.latestRevisionName" \
    --output tsv)
```

### WinError 5 в Azure CLI (Windows)

```powershell
$env:AZURE_EXTENSION_DIR = Join-Path $HOME '.az-extensions'
$env:AZURE_CONFIG_DIR = Join-Path $HOME '.az-cli'
```

### Проблемы с SSE/Streamable HTTP

```bash
# Проверка заголовков
curl -v -H "Accept: text/event-stream" \
  https://mcp.example.com/sse/

# Проверка MCP endpoint
curl -v -H "Accept: application/json, text/event-stream" \
  https://mcp.example.com/mcp/

# Проверка редиректов
curl -v -L https://mcp.example.com/mcp
```

## Масштабирование

### Azure Container Apps

```bash
# Автомасштабирование
az containerapp update \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --min-replicas 1 \
  --max-replicas 10 \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 100
```

### Kubernetes HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: taiga-mcp
  namespace: taiga-mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: taiga-mcp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Безопасность деплоя

### HTTPS

Всегда используйте HTTPS в production:

```bash
# Azure Container Apps (автоматически)
az containerapp update \
  --resource-group $AZURE_RESOURCE_GROUP \
  --name $AZURE_CONTAINER_APP \
  --ingress external \
  --target-port 8010

# Kubernetes (с cert-manager)
# См. пример Ingress выше
```

### Секреты

Никогда не храните секреты в образе или коде:

- **Azure:** Container Apps Secrets
- **Kubernetes:** Secrets + sealed-secrets/external-secrets
- **Docker:** env-file (не коммитьте!)

### Сетевая изоляция

```bash
# Azure Container Apps с VNet
az containerapp env create \
  --name taiga-mcp-env \
  --resource-group $AZURE_RESOURCE_GROUP \
  --location eastus \
  --infrastructure-subnet-resource-id $SUBNET_ID
```

## Рекомендуемая архитектура production

```
┌─────────────────────────────────────────┐
│              CDN / WAF                   │
│         (CloudFlare / Azure Front Door)  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           Load Balancer                  │
│         (Azure Ingress / Nginx)         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Taiga MCP Server                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Replica │  │ Replica │  │ Replica │ │
│  │   1     │  │   2     │  │   N     │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           Taiga Instance                 │
│      (self-hosted / taiga.io)           │
└─────────────────────────────────────────┘
```
