# Sprint 6: 打磨 & 發布

**Sprint 目標**: 完成端到端測試、性能優化和生產部署準備
**週期**: Week 13-14 (2 週)
**Story Points**: 35 點
**焦點**: 測試、優化、部署

---

## Sprint 概覽

### 目標
1. 完成端到端 (E2E) 測試
2. 執行性能測試和優化
3. 完成安全審計
4. 準備生產部署
5. 完成用戶文檔

### 成功標準
- [ ] E2E 測試覆蓋所有關鍵流程
- [ ] API 響應時間 P95 < 500ms
- [ ] 安全掃描無高危漏洞
- [ ] 生產環境部署成功
- [ ] 用戶手冊完成

---

## 發布前檢查清單

### 功能驗證

| 功能 | Sprint | 狀態 | 驗證方式 |
|------|--------|------|---------|
| F1: Agent 編排 | Sprint 1 | - | 順序執行測試 |
| F2: Human-in-the-loop | Sprint 2 | - | 審批流程測試 |
| F3: 跨系統集成 | Sprint 2 | - | 連接器測試 |
| F4: 跨場景協作 | Sprint 3 | - | 路由測試 |
| F5: Few-shot Learning | Sprint 4 | - | 學習案例測試 |
| F6: Agent 模板 | Sprint 4 | - | 實例化測試 |
| F7: DevUI | Sprint 4 | - | 追蹤測試 |
| F8: n8n 觸發 | Sprint 3 | - | Webhook 測試 |
| F9: Prompt 管理 | Sprint 3 | - | 模板測試 |
| F10: 審計追蹤 | Sprint 3 | - | 日誌查詢測試 |
| F11: Teams 通知 | Sprint 3 | - | 通知發送測試 |
| F12: 監控儀表板 | Sprint 5 | - | 指標顯示測試 |
| F13: Web UI | Sprint 5 | - | UI 功能測試 |
| F14: Redis 緩存 | Sprint 2 | - | 緩存命中測試 |

---

## User Stories

### S6-1: 端到端測試 (10 點)

**描述**: 作為 QA，我需要完整的 E2E 測試套件來驗證系統功能。

**驗收標準**:
- [ ] 所有關鍵業務流程有 E2E 測試
- [ ] 測試可在 CI 中自動運行
- [ ] 測試報告可視化
- [ ] 覆蓋率達到 80%+

**技術任務**:

1. **E2E 測試框架設置**
```python
# tests/e2e/conftest.py
import pytest
from httpx import AsyncClient
from main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(client):
    # 登錄並獲取 token
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword",
    })
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
```

2. **完整工作流 E2E 測試**
```python
# tests/e2e/test_workflow_lifecycle.py
import pytest


class TestWorkflowLifecycle:
    """工作流完整生命週期測試"""

    @pytest.mark.e2e
    async def test_complete_workflow_execution(self, authenticated_client):
        """測試從創建到完成的完整流程"""
        client = authenticated_client

        # 1. 創建 Agent
        agent_response = await client.post("/api/v1/agents/", json={
            "name": "E2E Test Agent",
            "instructions": "You are a test agent",
        })
        assert agent_response.status_code == 200
        agent_id = agent_response.json()["id"]

        # 2. 創建 Workflow
        workflow_response = await client.post("/api/v1/workflows/", json={
            "name": "E2E Test Workflow",
            "graph_definition": {
                "nodes": [
                    {"id": "start", "type": "start"},
                    {"id": "agent1", "type": "agent", "agent_id": agent_id},
                    {"id": "end", "type": "end"},
                ],
                "edges": [
                    {"source": "start", "target": "agent1"},
                    {"source": "agent1", "target": "end"},
                ],
            },
        })
        assert workflow_response.status_code == 200
        workflow_id = workflow_response.json()["id"]

        # 3. 執行 Workflow
        execute_response = await client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json={"message": "Hello E2E Test"},
        )
        assert execute_response.status_code == 200
        execution_id = execute_response.json()["execution_id"]

        # 4. 等待執行完成
        import asyncio
        for _ in range(30):  # 最多等待 30 秒
            status_response = await client.get(f"/api/v1/executions/{execution_id}")
            status = status_response.json()["status"]
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # 5. 驗證結果
        assert status == "completed"

        # 6. 檢查審計日誌
        audit_response = await client.get(
            f"/api/v1/audit/executions/{execution_id}/trail"
        )
        assert audit_response.status_code == 200
        assert len(audit_response.json()) > 0

        # 7. 清理
        await client.delete(f"/api/v1/workflows/{workflow_id}")
        await client.delete(f"/api/v1/agents/{agent_id}")


    @pytest.mark.e2e
    async def test_human_approval_flow(self, authenticated_client):
        """測試人機協作審批流程"""
        client = authenticated_client

        # 1. 創建帶審批節點的工作流
        # 2. 觸發執行
        # 3. 驗證暫停在審批節點
        # 4. 執行審批
        # 5. 驗證恢復執行
        # 6. 驗證完成
        pass
```

---

### S6-2: 性能測試與優化 (8 點)

**描述**: 作為 DevOps，我需要確保系統滿足性能要求。

**驗收標準**:
- [ ] API P95 響應時間 < 500ms
- [ ] 併發 50+ 用戶支持
- [ ] 緩存命中率 >= 60%
- [ ] 無內存洩漏

**技術任務**:

1. **負載測試腳本 (tests/load/locustfile.py)**
```python
from locust import HttpUser, task, between


class IPAUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 登錄
        response = self.client.post("/api/v1/auth/login", json={
            "email": "load_test@example.com",
            "password": "testpassword",
        })
        self.token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/stats")

    @task(2)
    def list_workflows(self):
        self.client.get("/api/v1/workflows/")

    @task(2)
    def list_agents(self):
        self.client.get("/api/v1/agents/")

    @task(1)
    def execute_workflow(self):
        self.client.post(
            "/api/v1/workflows/{workflow_id}/execute",
            json={"message": "Load test message"},
        )

    @task(1)
    def view_pending_approvals(self):
        self.client.get("/api/v1/checkpoints/pending")
```

2. **性能優化項目**
```python
# 數據庫查詢優化
- [ ] 添加缺失索引
- [ ] 優化 N+1 查詢
- [ ] 實現連接池

# 緩存優化
- [ ] 增加緩存覆蓋
- [ ] 優化緩存鍵策略
- [ ] 實現緩存預熱

# API 優化
- [ ] 添加響應壓縮
- [ ] 實現 ETag
- [ ] 優化序列化
```

---

### S6-3: 安全審計 (7 點)

**描述**: 作為安全工程師，我需要確保系統無高危漏洞。

**驗收標準**:
- [ ] OWASP Top 10 檢查通過
- [ ] 依賴漏洞掃描通過
- [ ] 認證/授權測試通過
- [ ] 敏感數據加密驗證

**技術任務**:

1. **安全檢查清單**
```yaml
authentication:
  - [ ] JWT 簽名驗證
  - [ ] Token 過期處理
  - [ ] 密碼強度要求
  - [ ] 登錄嘗試限制

authorization:
  - [ ] 角色權限驗證
  - [ ] 資源所有權檢查
  - [ ] API 端點保護

data_protection:
  - [ ] 敏感數據加密 (AES-256)
  - [ ] 傳輸加密 (TLS 1.3)
  - [ ] 密鑰管理 (Key Vault)

input_validation:
  - [ ] SQL 注入防護
  - [ ] XSS 防護
  - [ ] CSRF 防護
  - [ ] 請求大小限制

dependencies:
  - [ ] pip-audit 掃描
  - [ ] npm audit 掃描
  - [ ] 無高危漏洞
```

2. **安全測試腳本**
```python
# tests/security/test_auth.py
import pytest


class TestAuthentication:

    async def test_invalid_token_rejected(self, client):
        response = await client.get(
            "/api/v1/workflows/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    async def test_expired_token_rejected(self, client):
        # 使用過期 token
        pass

    async def test_sql_injection_prevented(self, client):
        response = await client.get(
            "/api/v1/workflows/?search='; DROP TABLE workflows; --"
        )
        assert response.status_code == 200  # 查詢正常，不會執行注入
```

---

### S6-4: 生產部署 (7 點)

**描述**: 作為 DevOps，我需要將系統部署到生產環境。

**驗收標準**:
- [ ] Azure 資源已配置
- [ ] CI/CD Pipeline 已設置
- [ ] 監控告警已配置
- [ ] 回滾計劃已準備

**技術任務**:

1. **部署架構**
```
Azure 生產環境

┌─────────────────────────────────────────────────────────────┐
│                    Azure Front Door                          │
│                    (WAF + CDN + SSL)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                Azure App Service                             │
│                (Python FastAPI)                              │
│                2 instances (B1 → S1)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│   PostgreSQL  │ │     Redis     │ │  Service Bus  │
│   Flexible    │ │     Cache     │ │               │
│   Server      │ │               │ │               │
└───────────────┘ └───────────────┘ └───────────────┘
        │
┌───────▼───────────────────────────────────────────┐
│              Application Insights                  │
│              (APM + Logging + Metrics)            │
└───────────────────────────────────────────────────┘
```

2. **部署腳本 (deploy/deploy.sh)**
```bash
#!/bin/bash
set -e

echo "=== IPA Platform 生產部署 ==="

# 變量
RESOURCE_GROUP="rg-ipa-platform-prod"
APP_NAME="app-ipa-platform-prod"
IMAGE_TAG="${1:-latest}"

# 1. 構建鏡像
echo "Building Docker image..."
docker build -t ipa-platform:$IMAGE_TAG -f backend/Dockerfile backend/

# 2. 推送到 ACR
echo "Pushing to Azure Container Registry..."
az acr login --name ipaplatformacr
docker tag ipa-platform:$IMAGE_TAG ipaplatformacr.azurecr.io/ipa-platform:$IMAGE_TAG
docker push ipaplatformacr.azurecr.io/ipa-platform:$IMAGE_TAG

# 3. 部署到 App Service
echo "Deploying to App Service..."
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --docker-custom-image-name ipaplatformacr.azurecr.io/ipa-platform:$IMAGE_TAG

# 4. 運行數據庫遷移
echo "Running database migrations..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings RUN_MIGRATIONS=true

# 5. 健康檢查
echo "Waiting for deployment..."
sleep 30

HEALTH_URL="https://${APP_NAME}.azurewebsites.net/health"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $HTTP_STATUS -eq 200 ]; then
  echo "✅ 部署成功! 應用運行正常。"
else
  echo "❌ 部署失敗! 健康檢查返回 $HTTP_STATUS"
  exit 1
fi

echo "=== 部署完成 ==="
```

---

### S6-5: 用戶文檔 (3 點)

**描述**: 作為產品經理，我需要完整的用戶文檔。

**驗收標準**:
- [ ] 快速開始指南
- [ ] 功能使用說明
- [ ] FAQ 文檔
- [ ] API 文檔

**文檔結構**:
```
docs/
├── user-guide/
│   ├── quick-start.md          # 快速開始
│   ├── dashboard.md            # Dashboard 使用
│   ├── workflows.md            # 工作流管理
│   ├── agents.md               # Agent 管理
│   ├── approvals.md            # 審批使用
│   └── faq.md                  # 常見問題
├── admin-guide/
│   ├── installation.md         # 安裝部署
│   ├── configuration.md        # 配置說明
│   ├── monitoring.md           # 監控設置
│   └── troubleshooting.md      # 故障排除
└── api-reference/
    └── openapi.yaml            # API 規格
```

---

## 發布時間線

### Week 13 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S6-1: E2E 測試框架 | QA | conftest.py |
| Day 2-3 | S6-1: 核心流程測試 | QA | 測試用例 |
| Day 3-4 | S6-2: 負載測試 | DevOps | locustfile.py |
| Day 4-5 | S6-2: 性能優化 | Backend | 優化代碼 |

### Week 14 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S6-3: 安全審計 | Security | 審計報告 |
| Day 7-8 | S6-4: 部署準備 | DevOps | 部署腳本 |
| Day 8-9 | S6-4: 生產部署 | DevOps | 部署驗證 |
| Day 9-10 | S6-5: 文檔完善 + 發布 | 全員 | 發布文檔 |

---

## 發布檢查清單

### 發布前一天
- [ ] 所有測試通過
- [ ] 安全掃描通過
- [ ] 性能測試達標
- [ ] 文檔已更新
- [ ] 回滾計劃已準備
- [ ] 監控告警已配置

### 發布當天
- [ ] 團隊成員在線
- [ ] 執行部署腳本
- [ ] 健康檢查通過
- [ ] 冒煙測試通過
- [ ] 監控正常

### 發布後
- [ ] 監控系統 24 小時
- [ ] 收集用戶反饋
- [ ] 記錄問題和改進
- [ ] 更新知識庫

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] 14 個 MVP 功能全部可用
   - [ ] E2E 測試覆蓋率 >= 80%

2. **性能達標**
   - [ ] API P95 < 500ms
   - [ ] 首屏加載 < 2 秒
   - [ ] 緩存命中率 >= 60%

3. **安全達標**
   - [ ] 無高危漏洞
   - [ ] 認證授權正常
   - [ ] 數據加密正確

4. **部署完成**
   - [ ] 生產環境運行
   - [ ] 監控告警配置
   - [ ] 文檔完整

---

## 相關文檔

- [Sprint 6 Checklist](./sprint-6-checklist.md)
- [Sprint 5 Plan](./sprint-5-plan.md) - 前置 Sprint
- [部署指南](../deployment-guide.md)
- [運維手冊](../operations-guide.md)
