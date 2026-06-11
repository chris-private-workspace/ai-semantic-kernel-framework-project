# IPA Platform 配置指南

本指南介紹 IPA Platform 的詳細配置選項。

---

## 目錄

1. [環境變數](#環境變數)
2. [數據庫配置](#數據庫配置)
3. [Redis 配置](#redis-配置)
4. [安全配置](#安全配置)
5. [AI 服務配置](#ai-服務配置)
6. [整合配置](#整合配置)

---

## 環境變數

### 必要變數

```bash
# ===================
# 應用程式配置
# ===================
APP_NAME=ipa-platform
APP_ENV=production          # development, staging, production
APP_DEBUG=false
APP_SECRET_KEY=<32-byte-secret>

# ===================
# 數據庫配置
# ===================
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_ECHO=false              # SQL 日誌

# ===================
# Redis 配置
# ===================
REDIS_URL=redis://:password@host:6379/0
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5

# ===================
# JWT 配置
# ===================
JWT_SECRET_KEY=<secure-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ===================
# Azure OpenAI 配置
# ===================
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
```

### 可選變數

```bash
# ===================
# 日誌配置
# ===================
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json            # json, text
LOG_FILE=/var/log/ipa/app.log

# ===================
# CORS 配置
# ===================
CORS_ORIGINS=["https://app.example.com"]
CORS_ALLOW_CREDENTIALS=true

# ===================
# 速率限制
# ===================
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# ===================
# 加密配置
# ===================
ENCRYPTION_KEY=<32-byte-key>
ENCRYPTION_ALGORITHM=AES-256-GCM

# ===================
# 監控配置
# ===================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
JAEGER_ENABLED=true
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
```

---

## 數據庫配置

### 連接池設置

```python
# backend/src/infrastructure/database/config.py

DATABASE_CONFIG = {
    # 連接池大小
    "pool_size": int(os.getenv("DB_POOL_SIZE", 20)),

    # 最大溢出連接數
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 10)),

    # 連接超時 (秒)
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 30)),

    # 連接回收時間 (秒)
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 3600)),

    # 連接預檢
    "pool_pre_ping": True,

    # SQL 日誌
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
}
```

### 推薦設置

| 環境 | pool_size | max_overflow | 說明 |
|------|-----------|--------------|------|
| 開發 | 5 | 5 | 小型單機 |
| 測試 | 10 | 5 | 測試環境 |
| 生產 | 20-50 | 10 | 根據負載調整 |

### 數據庫遷移

```bash
# 創建遷移
alembic revision --autogenerate -m "description"

# 執行遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1

# 查看遷移歷史
alembic history
```

---

## Redis 配置

### 連接設置

```python
# backend/src/infrastructure/cache/config.py

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "password": os.getenv("REDIS_PASSWORD"),
    "db": int(os.getenv("REDIS_DB", 0)),

    # 連接池
    "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", 10)),

    # 超時設置
    "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", 5)),
    "socket_connect_timeout": int(os.getenv("REDIS_CONNECT_TIMEOUT", 5)),

    # 重試設置
    "retry_on_timeout": True,
}
```

### 緩存策略

```yaml
# 緩存 TTL 配置
cache_ttl:
  workflow_detail: 300      # 5 分鐘
  workflow_list: 60         # 1 分鐘
  execution_status: 30      # 30 秒
  user_session: 1800        # 30 分鐘
  api_response: 60          # 1 分鐘
```

---

## 安全配置

### JWT 配置

```python
# JWT 設置
JWT_CONFIG = {
    "secret_key": os.getenv("JWT_SECRET_KEY"),
    "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    "access_token_expire_minutes": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30)),
    "refresh_token_expire_days": int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7)),
}
```

### 密碼策略

```yaml
password_policy:
  min_length: 12
  require_uppercase: true
  require_lowercase: true
  require_digits: true
  require_special: true
  max_age_days: 90
  history_count: 5
```

### CORS 配置

```python
# CORS 設置
CORS_CONFIG = {
    "allow_origins": json.loads(os.getenv("CORS_ORIGINS", '["*"]')),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["X-Request-ID", "X-Trace-ID"],
}
```

### 速率限制

```python
# 速率限制配置
RATE_LIMIT_CONFIG = {
    "default": {
        "requests": 100,
        "window_seconds": 60,
    },
    "auth": {
        "requests": 10,
        "window_seconds": 60,
    },
    "api": {
        "requests": 1000,
        "window_seconds": 60,
    },
}
```

### 安全標頭

```python
# 安全標頭配置
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
```

---

## AI 服務配置

### Azure OpenAI

```yaml
azure_openai:
  endpoint: "https://<resource>.openai.azure.com/"
  api_version: "2024-02-01"

  deployments:
    default:
      name: "gpt-4o"
      max_tokens: 4096
      temperature: 0.7

    classifier:
      name: "gpt-4o-mini"
      max_tokens: 1024
      temperature: 0.3

    summarizer:
      name: "gpt-4o"
      max_tokens: 2048
      temperature: 0.5

  rate_limits:
    requests_per_minute: 60
    tokens_per_minute: 90000
```

### Agent 配置

```yaml
agents:
  ticket_classifier:
    model: "gpt-4o-mini"
    system_prompt: |
      You are an IT ticket classifier. Analyze the ticket
      and classify it into: hardware, software, network, or other.
    temperature: 0.3
    max_tokens: 500

  customer_service:
    model: "gpt-4o"
    system_prompt: |
      You are a helpful customer service agent. Respond
      professionally and helpfully to customer inquiries.
    temperature: 0.7
    max_tokens: 1000
    tools:
      - search_knowledge_base
      - create_ticket
      - escalate_to_human
```

---

## 整合配置

### ServiceNow

```yaml
servicenow:
  instance_url: "https://your-instance.service-now.com"
  username: "${SERVICENOW_USERNAME}"
  password: "${SERVICENOW_PASSWORD}"

  api:
    table_api: "/api/now/table"
    import_set: "/api/now/import"

  mappings:
    incident:
      table: "incident"
      fields:
        - short_description
        - description
        - priority
        - assignment_group
```

### Microsoft Teams

```yaml
teams:
  tenant_id: "${TEAMS_TENANT_ID}"
  client_id: "${TEAMS_CLIENT_ID}"
  client_secret: "${TEAMS_CLIENT_SECRET}"

  notifications:
    default_channel: "ipa-notifications"
    error_channel: "ipa-alerts"
```

### n8n 整合

```yaml
n8n:
  base_url: "http://n8n:5678"
  api_key: "${N8N_API_KEY}"

  webhook:
    path: "/webhooks/n8n"
    secret: "${N8N_WEBHOOK_SECRET}"
```

---

## 配置最佳實踐

### 1. 使用環境變數

永遠不要在代碼中硬編碼敏感資訊：

```python
# ❌ 錯誤
API_KEY = "sk-abc123"

# ✅ 正確
API_KEY = os.getenv("API_KEY")
```

### 2. 使用 Secrets Manager

生產環境使用 Azure Key Vault：

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

db_password = client.get_secret("db-password").value
```

### 3. 環境分離

為每個環境使用不同的配置：

```
.env.development
.env.staging
.env.production
```

### 4. 配置驗證

啟動時驗證必要配置：

```python
def validate_config():
    required = [
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET_KEY",
        "AZURE_OPENAI_API_KEY",
    ]

    missing = [var for var in required if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required config: {missing}")
```

---

## 下一步

- [用戶管理](user-management.md) - 設置用戶和權限
- [故障排除](troubleshooting.md) - 常見問題解決
- [安裝指南](installation.md) - 部署說明

---

*最後更新: 2025-11-26*
