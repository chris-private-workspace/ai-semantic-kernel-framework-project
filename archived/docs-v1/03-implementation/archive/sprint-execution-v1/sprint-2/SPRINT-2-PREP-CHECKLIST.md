# Sprint 2 準備檢查清單

**創建日期**: 2025-11-25
**Sprint 期間**: 2025-12-23 至 2026-01-03 (2週)
**狀態**: 準備中

---

## 📋 Sprint 2 概覽

### 目標 Stories (8 個, 共 40 points)

| ID | 標題 | Points | 優先級 | 依賴 |
|----|------|--------|--------|------|
| S2-1 | n8n Webhook Integration | 8 | P0 | S1-3 |
| S2-2 | n8n Workflow Trigger | 5 | P0 | S2-1 |
| S2-3 | Teams Notification Service | 8 | P0 | S1-3 |
| S2-4 | Teams Approval Flow | 8 | P1 | S2-3, S1-5 |
| S2-5 | Monitoring Integration Service | 5 | P1 | S1-4 |
| S2-6 | Alert Manager Integration | 3 | P1 | S2-5 |
| S2-7 | Audit Log Service | 5 | P0 | S1-1 |
| S2-8 | Admin Dashboard APIs | 5 | P1 | S2-7 |

### 預期完成率
- **假期影響**: 12/23-1/3 期間團隊可用性降低 30-40%
- **預計完成**: 28-32 points (70-80%)
- **優先聚焦**: P0 Stories (S2-1, S2-2, S2-3, S2-7)

---

## ✅ 環境準備檢查清單

### 1. 基礎設施狀態 ✅

```bash
# 確認所有服務運行中
docker-compose ps
```

| 服務 | 狀態 | Port |
|------|------|------|
| ipa-postgres | ✅ Running | 5432 |
| ipa-redis | ✅ Running | 6379 |
| ipa-rabbitmq | ✅ Running | 5672, 15672 |
| ipa-kong | ✅ Running (healthy) | 8000, 8001 |
| ipa-kong-db | ✅ Running (healthy) | 5433 |
| ipa-backend | ✅ Running | 8080 |

### 2. Kong Gateway 配置 ⚠️

**已完成**:
- ✅ 4 Services 配置 (workflow, agent, auth, health)
- ✅ 6 Routes 配置
- ✅ Rate Limiting (3 services)
- ✅ CORS (3 services)
- ✅ File Logging
- ✅ Correlation ID

**待完成** (遺留項目):
- ⏳ JWT Plugin 配置
- ⏳ Consumer 創建
- ⏳ JWT Credentials 設置

### 3. Sprint 2 新增服務需求

#### S2-1, S2-2: n8n 整合

**本地測試環境選項**:

```yaml
# docker-compose.override.yml (可選)
services:
  n8n:
    image: n8nio/n8n
    container_name: ipa-n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin123
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://host.docker.internal:8000
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - ipa-network
```

**環境變數** (`.env`):
```bash
# n8n Webhook Configuration
N8N_WEBHOOK_SECRET=your-webhook-secret-key-here
N8N_BASE_URL=http://localhost:5678
```

#### S2-3, S2-4: Teams 通知

**本地開發策略** (無需 Teams 連接):
- Phase 1: Console/Mock 通知 (本地開發)
- Phase 2: 實際 Teams Webhook 連接 (可選)

**環境變數** (`.env`):
```bash
# Microsoft Teams Configuration (本地可使用 Mock)
TEAMS_WEBHOOK_URL=mock://console
TEAMS_NOTIFICATION_ENABLED=true
TEAMS_MOCK_MODE=true
```

**生產環境變數**:
```bash
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
TEAMS_NOTIFICATION_ENABLED=true
TEAMS_MOCK_MODE=false
```

#### S2-5, S2-6: 監控整合

**Prometheus 配置** (可選):

```yaml
# docker-compose.override.yml
services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: ipa-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - ipa-network
```

**環境變數**:
```bash
# Monitoring Configuration
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
OPENTELEMETRY_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---

## 🔧 技術準備

### 1. Python 依賴 (requirements.txt 更新)

```txt
# Sprint 2 新增依賴
# n8n Webhook Integration
hmac  # 內建模組
hashlib  # 內建模組

# Teams Notifications
httpx>=0.25.0  # 已安裝

# Monitoring
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-exporter-prometheus>=0.41b0
opentelemetry-instrumentation-fastapi>=0.41b0
prometheus-client>=0.17.1

# Audit Logging (使用現有 SQLAlchemy)
```

### 2. 資料庫 Schema (Alembic Migration)

```python
# Sprint 2 需要的新 Tables

# audit_logs - 審計日誌
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    action = Column(String(100), nullable=False)
    actor = Column(String(255), nullable=False)  # user_id or "system"
    resource_type = Column(String(100))  # workflow, execution, agent
    resource_id = Column(UUID)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))

# webhook_registrations - Webhook 註冊
class WebhookRegistration(Base):
    __tablename__ = "webhook_registrations"

    id = Column(UUID, primary_key=True)
    workflow_id = Column(UUID, ForeignKey("workflows.id"))
    source = Column(String(50))  # n8n, custom, etc.
    secret_key = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime)

# notification_templates - 通知模板
class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False)
    channel = Column(String(50))  # teams, email, slack
    template_type = Column(String(50))  # execution_success, execution_failed
    template_body = Column(JSON)  # Adaptive Card template
    is_active = Column(Boolean, default=True)
```

### 3. API 路由規劃

```
Sprint 2 新增 API Endpoints:

/api/v1/webhooks/
├── POST /n8n/{workflow_id}          # S2-1: 接收 n8n webhook
├── POST /n8n/{workflow_id}/test     # S2-1: 測試 webhook
└── GET  /registrations              # S2-1: 列出 webhook 註冊

/api/v1/notifications/
├── POST /send                       # S2-3: 發送通知
├── GET  /templates                  # S2-3: 獲取模板
└── POST /templates                  # S2-3: 創建模板

/api/v1/approvals/
├── GET  /pending                    # S2-4: 待審批列表
├── POST /{id}/approve               # S2-4: 批准
└── POST /{id}/reject                # S2-4: 拒絕

/api/v1/audit/
├── GET  /logs                       # S2-7: 審計日誌列表
├── GET  /logs/{id}                  # S2-7: 日誌詳情
└── GET  /logs/export                # S2-7: 導出日誌

/api/v1/admin/
├── GET  /dashboard                  # S2-8: Dashboard 統計
├── GET  /metrics                    # S2-8: 業務指標
└── GET  /health/detailed            # S2-8: 詳細健康狀態
```

---

## 📁 目錄結構規劃

```
backend/src/
├── api/v1/
│   ├── webhooks/                    # S2-1, S2-2
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── notifications/               # S2-3, S2-4
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── audit/                       # S2-7
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   └── admin/                       # S2-8
│       ├── __init__.py
│       ├── routes.py
│       └── schemas.py
├── domain/
│   ├── webhooks/                    # S2-1, S2-2
│   │   ├── service.py
│   │   └── n8n_handler.py
│   ├── notifications/               # S2-3, S2-4
│   │   ├── service.py
│   │   ├── teams_client.py
│   │   └── templates.py
│   ├── audit/                       # S2-7
│   │   ├── service.py
│   │   └── logger.py
│   └── admin/                       # S2-8
│       ├── service.py
│       └── metrics.py
├── infrastructure/
│   ├── database/models/
│   │   ├── audit_log.py
│   │   ├── webhook_registration.py
│   │   └── notification_template.py
│   └── monitoring/                  # S2-5, S2-6
│       ├── prometheus.py
│       ├── opentelemetry.py
│       └── alert_manager.py
```

---

## 🚀 Sprint 2 建議執行順序

### Week 1 (12/23-12/27) - 假期週
**可用性**: ~60%

1. **S2-7: Audit Log Service** (5 points) - P0
   - 基礎且獨立，可並行開發
   - 為其他 Stories 提供審計支持

2. **S2-1: n8n Webhook Integration** (8 points) - P0
   - 核心整合功能
   - 完成後 S2-2 可開始

### Week 2 (12/30-01/03) - 假期週
**可用性**: ~50%

3. **S2-3: Teams Notification Service** (8 points) - P0
   - 使用 Mock 模式先完成核心邏輯
   - 完成後 S2-4 可開始

4. **S2-2: n8n Workflow Trigger** (5 points) - P0
   - 依賴 S2-1 完成

### 如時間允許

5. **S2-5: Monitoring Integration** (5 points) - P1
6. **S2-8: Admin Dashboard APIs** (5 points) - P1
7. **S2-4: Teams Approval Flow** (8 points) - P1
8. **S2-6: Alert Manager Integration** (3 points) - P1

---

## ⚠️ 風險與緩解措施

### 1. 假期可用性風險
- **風險**: 團隊成員假期，可用性降低 30-40%
- **緩解**: 優先完成 P0 Stories，P1 可延至 Sprint 3

### 2. n8n 整合複雜度
- **風險**: n8n Webhook 簽名驗證可能有邊緣案例
- **緩解**: 使用標準 HMAC-SHA256，參考 n8n 官方文檔

### 3. Teams 連接問題
- **風險**: 本地無法連接 Teams
- **緩解**: 使用 Mock 模式開發，生產環境再連接

### 4. 資料庫 Migration
- **風險**: 新 Tables 可能與現有 Schema 衝突
- **緩解**: 使用 Alembic 管理，先在本地測試

---

## 📝 待辦事項 (Sprint 2 開始前)

### 必要 ✅
- [x] 確認基礎設施運行正常
- [x] 檢查 Sprint 2 規劃文檔
- [x] 確認 S1-8 JWT 遺留項目狀態

### 推薦 ⏳
- [ ] 完成 Kong JWT 配置 (可在 Sprint 2 期間完成)
- [ ] 準備 n8n 測試環境 (可使用 docker-compose.override.yml)
- [ ] 創建 Sprint 2 Database Migration

### 可選 📝
- [ ] 設置 Prometheus/Grafana (S2-5, S2-6 需要)
- [ ] 獲取 Teams Webhook URL (生產環境需要)

---

## 🎯 下一步行動

1. **立即**: 開始 S2-7 (Audit Log Service) 的設計
2. **Sprint 2 Day 1**: 創建 Sprint 2 feature branch
3. **每日**: 更新 sprint-status.yaml

---

**文檔最後更新**: 2025-11-25
