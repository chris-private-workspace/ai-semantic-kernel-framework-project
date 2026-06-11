# IPA Platform 安裝指南

本指南介紹如何安裝和部署 IPA Platform。

---

## 目錄

1. [系統需求](#系統需求)
2. [Docker 部署](#docker-部署)
3. [Kubernetes 部署](#kubernetes-部署)
4. [Azure 部署](#azure-部署)
5. [驗證安裝](#驗證安裝)

---

## 系統需求

### 最低配置

| 組件 | 最低需求 |
|------|----------|
| CPU | 4 核心 |
| 記憶體 | 8 GB |
| 磁碟 | 50 GB SSD |
| 網路 | 100 Mbps |

### 推薦配置

| 組件 | 推薦配置 |
|------|----------|
| CPU | 8+ 核心 |
| 記憶體 | 16+ GB |
| 磁碟 | 100+ GB SSD |
| 網路 | 1 Gbps |

### 軟體需求

| 軟體 | 版本 |
|------|------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| Kubernetes | 1.28+ (可選) |
| PostgreSQL | 16+ |
| Redis | 7+ |
| Node.js | 20+ (前端開發) |
| Python | 3.11+ (後端開發) |

---

## Docker 部署

### 步驟 1: 獲取代碼

```bash
git clone https://github.com/your-org/ipa-platform.git
cd ipa-platform
```

### 步驟 2: 配置環境變數

```bash
# 複製範例配置
cp .env.example .env

# 編輯配置
nano .env
```

**必要的環境變數**:

```bash
# 數據庫配置
DB_HOST=postgres
DB_PORT=5432
DB_NAME=ipa_platform
DB_USER=ipa_user
DB_PASSWORD=<secure-password>

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password>

# Azure OpenAI 配置
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# JWT 配置
JWT_SECRET_KEY=<generate-secure-key>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 加密配置
ENCRYPTION_KEY=<generate-32-byte-key>
```

### 步驟 3: 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 步驟 4: 初始化數據庫

```bash
# 執行數據庫遷移
docker-compose exec backend alembic upgrade head

# 創建初始管理員
docker-compose exec backend python scripts/create_admin.py
```

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Kubernetes 部署

### 步驟 1: 準備 Kubernetes 集群

確保您有可用的 Kubernetes 集群：
- Azure AKS
- AWS EKS
- Google GKE
- 或本地 Minikube

### 步驟 2: 創建命名空間

```bash
kubectl create namespace ipa-platform
```

### 步驟 3: 創建 Secrets

```bash
# 創建數據庫密鑰
kubectl create secret generic db-credentials \
  --from-literal=username=ipa_user \
  --from-literal=password=<secure-password> \
  -n ipa-platform

# 創建 Redis 密鑰
kubectl create secret generic redis-credentials \
  --from-literal=password=<secure-password> \
  -n ipa-platform

# 創建 Azure OpenAI 密鑰
kubectl create secret generic azure-openai \
  --from-literal=endpoint=https://<resource>.openai.azure.com/ \
  --from-literal=api-key=<your-api-key> \
  -n ipa-platform
```

### 步驟 4: 部署服務

```bash
# 部署 PostgreSQL
kubectl apply -f k8s/postgres.yaml -n ipa-platform

# 部署 Redis
kubectl apply -f k8s/redis.yaml -n ipa-platform

# 部署後端
kubectl apply -f k8s/backend.yaml -n ipa-platform

# 部署前端
kubectl apply -f k8s/frontend.yaml -n ipa-platform

# 部署 Ingress
kubectl apply -f k8s/ingress.yaml -n ipa-platform
```

### Kubernetes 部署清單

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ipa-platform/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
```

---

## Azure 部署

### 使用 Azure App Service

1. **創建資源群組**
```bash
az group create --name ipa-platform-rg --location eastasia
```

2. **創建 App Service Plan**
```bash
az appservice plan create \
  --name ipa-platform-plan \
  --resource-group ipa-platform-rg \
  --sku P1V2 \
  --is-linux
```

3. **創建 Web App**
```bash
az webapp create \
  --resource-group ipa-platform-rg \
  --plan ipa-platform-plan \
  --name ipa-platform-api \
  --runtime "PYTHON:3.11"
```

4. **配置環境變數**
```bash
az webapp config appsettings set \
  --resource-group ipa-platform-rg \
  --name ipa-platform-api \
  --settings \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=...)" \
    REDIS_URL="@Microsoft.KeyVault(SecretUri=...)"
```

### 使用 Azure Container Apps

```bash
# 創建 Container Apps 環境
az containerapp env create \
  --name ipa-platform-env \
  --resource-group ipa-platform-rg \
  --location eastasia

# 部署後端
az containerapp create \
  --name backend \
  --resource-group ipa-platform-rg \
  --environment ipa-platform-env \
  --image ipa-platform/backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10
```

---

## 驗證安裝

### 健康檢查

```bash
# API 健康檢查
curl http://localhost:8000/health

# 預期回應
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### 功能驗證

```bash
# 1. 驗證 API 可訪問
curl http://localhost:8000/api/v1/workflows

# 2. 驗證前端可訪問
curl http://localhost:3000

# 3. 驗證數據庫連接
docker-compose exec backend python -c "from src.infrastructure.database.session import engine; print('DB OK')"

# 4. 驗證 Redis 連接
docker-compose exec redis redis-cli -a <password> ping
```

### 常見問題

**問題: 數據庫連接失敗**
```
解決: 檢查 DATABASE_URL 配置和 PostgreSQL 服務狀態
docker-compose logs postgres
```

**問題: Redis 連接失敗**
```
解決: 檢查 REDIS_PASSWORD 配置
docker-compose exec redis redis-cli -a <password> ping
```

**問題: Azure OpenAI 呼叫失敗**
```
解決: 驗證 API Key 和 Endpoint 配置
curl -X POST $AZURE_OPENAI_ENDPOINT/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-02-01 \
  -H "api-key: $AZURE_OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

---

## 下一步

- [配置指南](configuration.md) - 詳細配置選項
- [用戶管理](user-management.md) - 設置用戶和權限
- [故障排除](troubleshooting.md) - 常見問題解決

---

*最後更新: 2025-11-26*
