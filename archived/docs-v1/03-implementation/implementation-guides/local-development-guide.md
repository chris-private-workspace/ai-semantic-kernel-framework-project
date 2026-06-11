# 本地開發指南

本文檔說明如何在**完全不依賴 Azure 服務**的情況下進行本地開發。

## 🎯 開發策略

### Phase 1: 純本地開發（推薦用於 Sprint 0-3）
- ✅ **零成本**：無需 Azure 訂閱
- ✅ **快速迭代**：無網絡延遲
- ✅ **離線開發**：不依賴網絡

### Phase 2: 混合模式（Sprint 4 集成測試）
- 本地：PostgreSQL, Redis, RabbitMQ
- Azure：Service Bus, Application Insights（僅用於測試）

### Phase 3: 完全雲端（Sprint 5+ 生產部署）
- 所有服務遷移到 Azure

---

## 🚀 快速開始（15 分鐘）

### 1. 前置要求
- Docker Desktop 20.10+
- Python 3.11+ (可選，如需修改後端代碼)
- Git

### 2. 克隆項目
```bash
git clone https://github.com/laitim2001/ai-semantic-kernel-framework-project.git
cd ai-semantic-kernel-framework-project
```

### 3. 配置環境變量
```bash
# 複製環境變量模板
cp .env.example .env

# 編輯 .env 文件（最小配置）
# Windows
notepad .env

# 需要設置的最小變量：
# OPENAI_API_KEY=sk-your-openai-api-key  # 從 https://platform.openai.com/ 獲取
```

### 4. 啟動所有服務
```bash
docker-compose up -d
```

### 5. 驗證服務
```bash
# 檢查所有容器狀態
docker-compose ps

# 應該看到 4 個服務都是 healthy:
# - ipa-postgres (PostgreSQL 16)
# - ipa-redis (Redis 7)
# - ipa-rabbitmq (RabbitMQ 3.12)
# - ipa-backend (FastAPI)

# 測試 API
curl http://localhost:8000/health

# 應該返回:
# {"status":"healthy","version":"0.1.0"}
```

### 6. 訪問管理界面
- **API 文檔**: http://localhost:8000/docs
- **RabbitMQ 管理**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: `localhost:5432` (ipa_user/ipa_password)
- **Redis**: `localhost:6379`

---

## 📦 服務說明

### PostgreSQL (數據庫)
- **端口**: 5432
- **用戶名**: ipa_user
- **密碼**: ipa_password
- **數據庫**: ipa_platform
- **連接字符串**: `postgresql://ipa_user:ipa_password@localhost:5432/ipa_platform`

**使用 psql 連接**:
```bash
docker-compose exec postgres psql -U ipa_user -d ipa_platform
```

### Redis (緩存)
- **端口**: 6379
- **密碼**: redis_password

**使用 redis-cli**:
```bash
docker-compose exec redis redis-cli -a redis_password
```

### RabbitMQ (消息隊列)
- **AMQP 端口**: 5672
- **管理界面**: http://localhost:15672
- **用戶名/密碼**: guest/guest

**創建測試消息**:
```bash
# 安裝 Python client
pip install pika

# 發送測試消息
python -c "
import pika
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='test')
channel.basic_publish(exchange='', routing_key='test', body='Hello World!')
print('Message sent!')
connection.close()
"
```

### Backend API (FastAPI)
- **端口**: 8000
- **API 文檔**: http://localhost:8000/docs
- **健康檢查**: http://localhost:8000/health

---

## 🔧 本地開發配置詳解

### 環境變量配置

```bash
# .env 文件（本地開發推薦配置）

# ============================================
# 數據庫配置（本地 Docker）
# ============================================
DATABASE_URL=postgresql://ipa_user:ipa_password@localhost:5432/ipa_platform
DB_HOST=localhost
DB_PORT=5432
DB_USER=ipa_user
DB_PASSWORD=ipa_password
DB_NAME=ipa_platform

# ============================================
# 緩存配置（本地 Docker）
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# ============================================
# 消息隊列配置（本地 RabbitMQ）
# ============================================
MESSAGE_QUEUE_TYPE=rabbitmq
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# ============================================
# 認證配置（Mock 模式 - 無需 Azure AD）
# ============================================
AUTH_MODE=mock
MOCK_USER_EMAIL=developer@example.com
MOCK_USER_NAME=Local Developer
MOCK_USER_ROLES=admin,user

# ============================================
# 日誌配置（控制台輸出）
# ============================================
LOGGING_MODE=console
LOG_LEVEL=DEBUG

# ============================================
# AI 配置（使用 OpenAI API）
# ============================================
# 選項 1: OpenAI (便宜，推薦開發用)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo  # $0.001/1K tokens (比 GPT-4 便宜 30 倍)

# 選項 2: Azure OpenAI (生產環境用 - 可選)
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-key

# ============================================
# 應用配置
# ============================================
APP_ENV=development
API_PORT=8000
```

---

## 🧪 開發工作流

### 修改後端代碼

```bash
# 1. 進入後端目錄
cd backend

# 2. 創建 Python 虛擬環境（首次）
python -m venv venv

# 3. 激活虛擬環境
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 修改代碼...
# 編輯 main.py, src/workflow/service.py 等

# 6. 重啟 backend 容器查看更改
docker-compose restart backend

# 7. 查看日誌
docker-compose logs -f backend
```

### 運行測試

```bash
# 在 backend/ 目錄下
pytest

# 查看覆蓋率
pytest --cov=src --cov-report=html

# 打開覆蓋率報告
start htmlcov/index.html  # Windows
```

### 數據庫遷移

```bash
# 稍後會添加 Alembic migrations
# 創建新遷移
alembic revision --autogenerate -m "Add new table"

# 執行遷移
alembic upgrade head
```

---

## 🔄 從本地遷移到 Azure（未來）

當 MVP 開發完成，準備部署時：

### 1. 更新環境變量

```bash
# .env.production
MESSAGE_QUEUE_TYPE=azure_service_bus
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...

AUTH_MODE=azure_ad
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id

LOGGING_MODE=application_insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

### 2. 代碼無需修改

所有服務都使用了抽象層，切換環境只需修改環境變量：

```python
# 代碼中使用統一接口
from src.messaging import get_message_publisher

publisher = get_message_publisher()  # 自動根據環境變量選擇 RabbitMQ 或 Service Bus
await publisher.publish("queue_name", message)
```

---

## 💰 成本對比

### 本地開發（Sprint 0-3，3 個月）
- Docker 容器: **免費**
- OpenAI API (gpt-3.5-turbo): ~**$20/月**
- **總計**: **$60 (3個月)**

### 如果使用 Azure 開發環境（不推薦）
- Azure PostgreSQL: $12/月
- Azure Redis: $16/月
- Azure Service Bus: $10/月
- Application Insights: $0 (免費額度)
- **總計**: **$114 (3個月) + $60 OpenAI = $174**

**節省**: **$114** (65% 成本降低)

---

## 🚨 常見問題

### Q1: 容器啟動失敗怎麼辦？

```bash
# 查看詳細日誌
docker-compose logs postgres
docker-compose logs redis
docker-compose logs rabbitmq
docker-compose logs backend

# 重新構建並啟動
docker-compose down -v  # 刪除所有數據卷
docker-compose up --build -d
```

### Q2: 端口衝突怎麼辦？

如果 5432/6379/5672 端口被占用：

```bash
# 修改 .env 文件
DB_PORT=5433
REDIS_PORT=6380
RABBITMQ_PORT=5673

# 或修改 docker-compose.yml
ports:
  - "5433:5432"  # 宿主機:容器
```

### Q3: 數據丟失怎麼辦？

Docker 數據卷會持久化數據：

```bash
# 查看數據卷
docker volume ls

# 備份 PostgreSQL
docker-compose exec postgres pg_dump -U ipa_user ipa_platform > backup.sql

# 恢復
docker-compose exec -T postgres psql -U ipa_user ipa_platform < backup.sql
```

### Q4: 什麼時候需要使用 Azure 服務？

**開發階段（現在）**: 完全不需要
**集成測試（Sprint 4）**: 可選，僅測試 Service Bus 集成
**生產部署（Sprint 5+）**: 必需，所有服務上雲

---

## 📚 相關文檔

- [docker-compose.yml](../docker-compose.yml) - 完整服務配置
- [.env.example](../.env.example) - 環境變量模板
- [Backend README](../backend/README.md) - 後端開發指南
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 貢獻指南

---

## 🆘 需要幫助？

如果遇到問題：
1. 查看 [故障排除](#common-issues) 部分
2. 查看 Docker 容器日誌：`docker-compose logs -f`
3. 在 GitHub 提交 Issue

---

**最後更新**: 2025-11-20  
**適用版本**: Sprint 0 - Sprint 3
